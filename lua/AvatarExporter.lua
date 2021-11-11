--!strict
if (plugin == nil) then
	print("This script needs to be run as Studio plugin.")
	return
end

local kServerUrl = "http://127.0.0.1:49999/"


local g_InsertService = game:GetService("InsertService")
local g_Players = game:GetService("Players")
local g_AssetService = game:GetService("AssetService")
local g_SelectionService = game:GetService("Selection")
local g_Http = game:GetService("HttpService")


local g_ObjectToId = {}
local g_UUID: number = 99


local function getUUID()
	g_UUID = g_UUID + 1
	return g_UUID
end


local function fixFileName(name)
	name = string.gsub(name, ' ', '_')
	name = string.gsub(name, "'", '_')
	name = string.gsub(name, '"', '_')
	name = string.gsub(name, "`", '_')
	name = string.gsub(name, ':', '_')
	name = string.gsub(name, '/', '_')
	name = string.gsub(name, '\\', '_')
	name = string.gsub(name, '.', '_')
	name = string.gsub(name, '@', '_')
	name = string.gsub(name, ',', '_')
	return name
end


local function createObjectGuid(object: Instance)
	local key = object:GetFullName()
	if g_ObjectToId[key] ~= nil then
		warn("WARNING! Key already exist: '" .. tostring(key) .. "'")
	else
		g_ObjectToId[key] = tostring(getUUID())
	end
end

local function getObjectGuid(object: Instance)
	local guid = -1
	if not object then
		return tostring(guid)
	end

	local key = object:GetFullName()	
	if g_ObjectToId[key] ~= nil then
		guid = g_ObjectToId[key]
	end
	return tostring(guid)
end

local function getCFrame(xform: CFrame)
	local tx,ty,tz,r00,r01,r02,r10,r11,r12,r20,r21,r22 = xform:GetComponents()

	local val = {}
	val["tx"] = tx
	val["ty"] = ty
	val["tz"] = tz

	val["r00"] = r00
	val["r01"] = r01
	val["r02"] = r02

	val["r10"] = r10
	val["r11"] = r11
	val["r12"] = r12

	val["r20"] = r20
	val["r21"] = r21
	val["r22"] = r22
	return val
end



local function getAvatarDescriptionRecursive(object: Instance, parent: Instance, depth: number, tableState)

	local isSupportedType = false
	if object:IsA("MeshPart") or
		object:IsA("Part") or
		object:IsA("Model") or
		object:IsA("Bone") or
		object:IsA("Attachment") or
		object:IsA("WeldConstraint") or
		object:IsA("Accessory") or
		object:IsA("Motor6D") then
		isSupportedType = true
	end

	if not isSupportedType then
		return
	end

	--print(">" .. tostring(depth) .. object:GetFullName())		

	if tableState == nil then
		createObjectGuid(object)	
	else
		local objectGuid = getObjectGuid(object)

		if tableState[objectGuid] == nil then
			local dmObject = {}
			dmObject["Name"] = object.Name
			dmObject["Class"] = object.ClassName
			dmObject["Parent"] = getObjectGuid(parent)

			if object:IsA("Model") then
				--print(object.PrimaryPart:GetFullName())
				dmObject["PrimaryPart"] = getObjectGuid(object.PrimaryPart)
			elseif object:IsA("Part") then

				dmObject["CFrame"] = getCFrame(object.CFrame)
				dmObject["SizeX"] = object.Size.X 
				dmObject["SizeY"] = object.Size.Y 
				dmObject["SizeZ"] = object.Size.Z

				local specialMesh = object:FindFirstChildWhichIsA("SpecialMesh")
				if specialMesh ~= nil then
					-- pretend like a special mesh is a regular mesh part
					dmObject["Class"] = "MeshPart"

					local meshType = "Unsupported"
					if specialMesh.MeshType == Enum.MeshType.Head then
						meshType = "Head"
					elseif specialMesh.MeshType == Enum.MeshType.Sphere then
						meshType = "Sphere"
					elseif specialMesh.MeshType == Enum.MeshType.FileMesh then
						meshType = "File"
					end

					dmObject["MeshType"] = meshType
					dmObject["MeshId"] = specialMesh.MeshId 
					dmObject["TextureId"] = specialMesh.TextureId 

					dmObject["OffsetX"] = specialMesh.Offset.X
					dmObject["OffsetY"] = specialMesh.Offset.Y
					dmObject["OffsetZ"] = specialMesh.Offset.Z
					dmObject["ScaleX"] = specialMesh.Scale.X
					dmObject["ScaleY"] = specialMesh.Scale.Y
					dmObject["ScaleZ"] = specialMesh.Scale.Z
				end
			elseif object:IsA("MeshPart") then
				dmObject["CFrame"] = getCFrame(object.CFrame)
				dmObject["MeshType"] = "File"
				dmObject["MeshId"] = object.MeshId 
				dmObject["TextureId"] = object.TextureID 

				dmObject["SizeX"] = object.Size.X 
				dmObject["SizeY"] = object.Size.Y 
				dmObject["SizeZ"] = object.Size.Z

				dmObject["OffsetX"] = 0
				dmObject["OffsetY"] = 0
				dmObject["OffsetZ"] = 0

				local originalSize = object:FindFirstChild("OriginalSize")
				if originalSize == nil then
					-- note: this is not exact engine behaviour!
					dmObject["ScaleX"] = 1.0
					dmObject["ScaleY"] = 1.0
					dmObject["ScaleZ"] = 1.0
				else
					dmObject["ScaleX"] = (object.Size.X / originalSize.Value.X)
					dmObject["ScaleY"] = (object.Size.Y / originalSize.Value.Y)
					dmObject["ScaleZ"] = (object.Size.Z / originalSize.Value.Z)
				end

			elseif object:IsA("Bone") then
				dmObject["CFrame"] = getCFrame(object.CFrame)
			elseif object:IsA("Accessory") then
				dmObject["AttachPoint"] = getCFrame(object.AttachmentPoint)
			elseif object:IsA("Attachment") then
				dmObject["CFrame"] = getCFrame(object.CFrame)
			elseif object:IsA("WeldConstraint") then
				dmObject["Part0"] = getObjectGuid(object.Part0)
				dmObject["Part1"] = getObjectGuid(object.Part1)				
			elseif object:IsA("Motor6D") then
				dmObject["Transform"] = getCFrame(object.Transform)
				dmObject["C0"] = getCFrame(object.C0)
				dmObject["C1"] = getCFrame(object.C1)
				dmObject["Part0"] = getObjectGuid(object.Part0)
				dmObject["Part1"] = getObjectGuid(object.Part1)				
			end

			tableState[objectGuid] = dmObject
			--print(object:GetFullName() .. ", " .. objectGuid)
		else
			warn("Sanity check failed. GUID intersection?")
			warn("Ignore object: '" .. object:GetFullName() .. "', " .. objectGuid)
		end	
	end

	local children = object:GetChildren()
	for index, descendant in ipairs(children) do
		getAvatarDescriptionRecursive(descendant, object, depth+1, tableState)	
	end
end

local function getSelectedAvatar()
	local selectedObjects = g_SelectionService:Get()
	if #selectedObjects ~= 1 then
		warn("Please select avatar model")
		return nil
	end

	local avatarModel = selectedObjects[1]
	if not avatarModel:IsA("Model") then
		warn("Selected instance is not a model")
		return nil
	end

	return avatarModel
end

local function createAvatarDescription(avatarModel: Model)
	if not avatarModel:IsA("Model") then
		warn("Selected instance is not a model")
		return nil
	end

	local rootPart = avatarModel:FindFirstChild("HumanoidRootPart")
	if rootPart == nil then
		warn("HumanoidRootPart not found!")
		return nil
	end

	-- reset table
	g_ObjectToId = {}

	-- 1st pass. Initialize all IDs
	getAvatarDescriptionRecursive(avatarModel, nil, 1, nil)

	--2nd pass. Actual work
	local avatarDesc = {}
	getAvatarDescriptionRecursive(avatarModel, nil, 1, avatarDesc)


	return g_Http:JSONEncode(avatarDesc)
end


local function createDefaultR15Rig()
	local assetId = 1664543044
	local success, model = pcall(g_InsertService.LoadAsset, g_InsertService, assetId)
	if success and model then
		local player = model:FindFirstChild("Player")
		if player then
			return player
		end
	end

	warn("Model failed to load Default rig!")
	return nil
end

local function applyHead(avatarModel, assetId)
	local success, model = pcall(g_InsertService.LoadAsset, g_InsertService, assetId)
	if success and model then
		local headFromBundle = model:FindFirstChildWhichIsA("SpecialMesh")
		if headFromBundle then
			local headPart = avatarModel:FindFirstChild("Head")
			if headPart then
				local existingSM = headPart:FindFirstChildWhichIsA("SpecialMesh")
				if existingSM then
					existingSM:Destroy()
				end
				headFromBundle.Parent = headPart 
			end
		end
		model:Destroy()

		local assetInfo = game:GetService("MarketplaceService"):GetProductInfo(assetId)
		
		local name = fixFileName(assetInfo.Name)
		return "Head_" .. name
	end

	return "None"
end

local function applyBundle(humanoid, bundleId)
	local bundleInfo = g_AssetService:GetBundleDetailsAsync(bundleId)
	local outfitId = 0

	-- Find the outfit that corresponds with this bundle.
	for _,item in pairs(bundleInfo.Items) do
		if item.Type == "UserOutfit" then
			outfitId = item.Id
			break
		end
	end

	if outfitId > 0 then
		local bundleDesc = g_Players:GetHumanoidDescriptionFromOutfitId(outfitId)
		humanoid:ApplyDescription(bundleDesc)
	end

	local name = fixFileName(bundleInfo.Name)
	return name
end

local function batchExport()

	local blankR15 = createDefaultR15Rig()
	if not blankR15 then
		warn("Can't create default R15 rig")
		return
	end

	blankR15.Parent = game.ReplicatedStorage

	local success, response = pcall(g_Http.GetAsync, g_Http, kServerUrl, false)
	if not success then
		warn("Http request failed. Please run FbxExporterServer.py")
		return
	end

	local response = g_Http:JSONDecode(response)
	print("heads count :" .. tostring(#response.heads) )
	print("bundles count :" .. tostring(#response.bundles) )

	for _, headId in ipairs(response.heads) do
		print("Spawning head " .. tostring(headId))
		local avatarModel = blankR15:Clone()
		avatarModel.Parent = workspace
		local name = applyHead(avatarModel, headId)
		avatarModel.Name = name
		local json = createAvatarDescription(avatarModel)
		if not json then
			warn("Can not generate avatar descriptor")
		else
			print("Waiting response from 'Avatar FBX Exporter Server'")
			local success, response = pcall(g_Http.PostAsync, g_Http, kServerUrl, json, Enum.HttpContentType.ApplicationJson, false)
			if not success then
				warn("Http request failed. Please run FbxExporterServer.py")
			end
			print(response)			
		end

		avatarModel:Destroy()
	end


	for _, bundleId in ipairs(response.bundles) do
		print("Spawning bundle " .. tostring(bundleId))
		local avatarModel = blankR15:Clone()
		avatarModel.Parent = workspace
		local name = applyBundle(avatarModel.Humanoid, bundleId)
		avatarModel.Name = name
		local json = createAvatarDescription(avatarModel)
		if not json then
			warn("Can not generate avatar descriptor")
		else
			print("Waiting response from 'Avatar FBX Exporter Server'")
			local success, response = pcall(g_Http.PostAsync, g_Http, kServerUrl, json, Enum.HttpContentType.ApplicationJson, false)
			if not success then
				warn("Http request failed. Please run FbxExporterServer.py")
			end
			print(response)			
		end

		avatarModel:Destroy()
	end

	blankR15:Destroy()

end


local g_Toolbar = plugin:CreateToolbar("Avatar")
local avatarExportBtn = g_Toolbar:CreateButton("Avatar Exporter", "Avatar FBX Exporter", "rbxassetid://6506010585")
avatarExportBtn.Click:connect(function()
	local avatarModel = getSelectedAvatar()
	if not avatarModel then
		return
	end
	assert(avatarModel)
	local json = createAvatarDescription(avatarModel)
	if not json then
		warn("Can not generate avatar descriptor")
		return
	end

	print("Waiting response from 'Avatar FBX Exporter Server'")
	local success, response = pcall(g_Http.PostAsync, g_Http, kServerUrl, json, Enum.HttpContentType.ApplicationJson, false)
	if not success then
		warn("Http request failed. Please run FbxExporterServer.py")
		return
	end
	print(response)
end)


local batchExportBtn = g_Toolbar:CreateButton("Batch Export", "Batch Export", "rbxassetid://6506875534")
batchExportBtn.Click:connect(function()
	batchExport()	
end)

