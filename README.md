# RobloxAvatarExporter

Standalone Avatar Exporter + Batch Exporter


# How to use (single avatar export)

1. Clone repo
2. Install the following plugin (or create a local plugin using source code from this repo)  
   https://www.roblox.com/library/6506050633/AvatarExporter  
   ![alt tag](https://raw.githubusercontent.com/SergeyMakeev/RobloxAvatarExporter/master/pics/plugin.png)
4. Run `python FbxExporterServer.py`
5. Open Roblox Studio and select an avatar you need to export  
   ![alt tag](https://raw.githubusercontent.com/SergeyMakeev/RobloxAvatarExporter/master/pics/select_avatar.png)
6. Click `Avatar Exporter` button
7. Find the resulting `.FBX` file in the `Avatars` folder

# How to use (batch export)

1. Clone repo
2. Install the following plugin (or create a local plugin using source code from this repo)  
   https://www.roblox.com/library/6506050633/AvatarExporter
3. Open `bundles.txt` (or `accessories.txt`) and type a list of avatar bundles you want to export
4. Run `python FbxExporterServer.py`
5. Open Roblox Studio and create an empty base plate
6. Click `Batch Export` button
7. Find the resulting avatar bundles exported to `.FBX` files in the `Avatars` folder
   ![alt tag](https://raw.githubusercontent.com/SergeyMakeev/RobloxAvatarExporter/master/pics/fbx_avatar.png)
   
