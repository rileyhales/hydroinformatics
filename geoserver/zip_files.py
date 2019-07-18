import zipfile, os

path = '/Users/rileyhales/tethys/apps/gldas/tethysapp/gldas/workspaces/user_workspaces/admin'
files = os.listdir('/Users/rileyhales/tethys/apps/gldas/tethysapp/gldas/workspaces/user_workspaces/admin')
archive = zipfile.ZipFile('/Users/rileyhales/hydroinformatics/admin.zip', mode='w')
for file in files:
    archive.write(os.path.join(path, file), arcname=file)
archive.close()
