QT.3dinput.VERSION = 5.15.8
QT.3dinput.name = Qt3DInput
QT.3dinput.module = Qt3DInput
QT.3dinput.libs = $$QT_MODULE_LIB_BASE
QT.3dinput.includes = $$QT_MODULE_LIB_BASE/Qt3DInput.framework/Headers
QT.3dinput.frameworks = $$QT_MODULE_LIB_BASE
QT.3dinput.bins = $$QT_MODULE_BIN_BASE
QT.3dinput.plugin_types = 3dinputdevices
QT.3dinput.depends = core gui 3dcore gamepad
QT.3dinput.uses =
QT.3dinput.module_config = v2 lib_bundle
QT.3dinput.DEFINES = QT_3DINPUT_LIB
QT.3dinput.enabled_features =
QT.3dinput.disabled_features =
QT_CONFIG +=
QT_MODULES += 3dinput