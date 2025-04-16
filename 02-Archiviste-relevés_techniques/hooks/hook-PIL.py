from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Inclure tous les sous-modules de PIL
hiddenimports = collect_submodules('PIL')

# Inclure les fichiers de données associés à PIL (comme les fichiers binaires compilés)
datas = collect_data_files('PIL')
