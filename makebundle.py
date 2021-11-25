#!/usr/bin/env python3

SCRIPT_VERSION = "0.17"

import os
import sys
import subprocess
import distutils.dir_util
import shutil
import fnmatch

SYS_LIBS = [
    "/System/*",
    "/usr/lib/libobjc.*.dylib",
    "/usr/lib/libSystem.*.dylib",
    "/usr/lib/libiconv.2.dylib",
    "/usr/lib/libncurses.5.4.dylib",
    "/usr/lib/libc++.1.dylib",
    "/usr/lib/libz.1.dylib",
    "/usr/lib/libbz*.dylib",
    "/usr/lib/libxar.*.dylib",
    "/usr/lib/libcups.*.dylib",
]


DEBUG = False

#######################################
# Utility functions
#######################################

def info(*args):
    print("\33[94m", end='')
    print(*args, end='')
    print("\u001b[0m")


def debug(*args):
    if DEBUG:
        print("\33[36m", end='')
        print(*args, end='')
        print("\u001b[0m")


def error(*args):
    print("\33[91m", end='')
    print(*args, end='')
    print("\u001b[0m")


def call(*args):
    try:
        #print(type(list(args)), print(list(args)))
        subprocess.check_call(list(args))
    except subprocess.CalledProcessError as err:
        error(err)
        sys.exit(1)


def isMacho(file):
    magic  = b'\xfe\xed\xfa\xcf'  # The 64-bit mach magic number
    magic2 = b'\xcf\xfa\xed\xfe'  # NXSwapInt(MH_MAGIC_64)

    with open(file, 'rb') as f:
        data = f.read(4)
        return (data == magic or data == magic2)



#######################################
# Step functions
#######################################

def extract(file, outDir):
    debug(f"Extract {file} to {outDir}")

    call(
        "tar",
        "xf", file,
        "--directory=%s" % outDir,
        "--strip", "1",
    )


def mkdir(path):
    debug(f"Create directory {path}")
    os.makedirs(path, exist_ok=True)


def rmdir(dir):
    try:
        shutil.rmtree(str(dir))
    except FileNotFoundError:
        pass
    except OSError as err:
        error("Can't delete %s : %s" % (dir, err.strerror))
        sys.exit(1)


def rmfile(file):
    if os.path.exists(file):
        os.remove(file)

def cmake(*args):
    debug("Run cmake:",  " ".join(args))
    call("cmake", *args)


def make(*args):
    debug("Run make:",  " ".join(args))
    call("make", *args)


def copy(src, dest):
    debug("COPY ", src, dest)

    if os.path.isdir(src):
        if os.path.isdir(dest):
            dest = dest + "/" + os.path.basename(src)
        distutils.dir_util.copy_tree(src, dest, preserve_symlinks=True)

    else:
        shutil.copy2(src, dest, follow_symlinks=False)


def checkDyLibs(bundleDir):
    errors = []
    def checkLib(fileName, lib):
        f = lib.replace("@executable_path",  f"{bundleDir}/Contents/MacOS")

        if not os.path.exists(f):
            errors.append(f"Library not found: {f}")

    def isSystemLib(lib):
        for s in SYS_LIBS:
            if fnmatch.fnmatchcase(lib, s):
                return True
        return False

    res = True
    for (dirpath, dirnames, filenames) in os.walk(bundleDir):

        for f in filenames:
            errors = []
            fileName = f"{dirpath}/{f}"
            lines = subprocess.check_output(["otool", "-L", fileName])
            lines = lines.split(b"\n")

            for line in lines[1:]:
                line = line.decode("UTF-8").strip()
                if line == "":
                    continue

                lib = line[:line.index("(")].strip()

                if isSystemLib(lib):
                    continue

                if lib.startswith("@executable_path/../Frameworks/"):
                    checkLib(fileName, lib)
                    continue

                suffix = fileName.removeprefix(f"{bundleDir}/Contents/PlugIns/")
                if lib.endswith(suffix):
                    continue

                if os.path.basename(lib) == os.path.basename(fileName):
                    continue

                errors.append(f"Non local libreary - {lib}")

            if errors:
                res = False
                print(f"{fileName}")
                for e in errors:
                    error(f"- {e}")


    if not res:
        sys.exit(2)


#===========================================
#
def checkArch(bundleDir, archs):
    for (dirpath, dirnames, filenames) in os.walk(bundleDir):

        res = True
        for f in filenames:
            fileName = f"{dirpath}/{f}"
            try:
                if isMacho(fileName):
                    r = subprocess.check_call(["lipo", fileName, "-verify_arch"] + archs)
                    print(r, archs)
            except subprocess.CalledProcessError:
                f = fileName.removeprefix(bundleDir + "/")
                error(f"The {' and '.join(archs)} architectures are not supported by   {f}")
                res = False

    if not res:
        sys.exit(2)

#===========================================
#
def signBundle(bundlePath, certIdentity):
    call("codesign",
        "--force",
        "--deep",
        "--verify",
        "--sign",  f"{certIdentity}",
        bundlePath
    )

    call("codesign",
        "--all-architectures",
        "-v",
        "--strict",
        "--deep",
        "--verbose=1",
         bundlePath
    )

    call("spctl",
        "--assess",
        "--type",
        "execute",
        bundlePath
    )


#===========================================
#
# class Dmg:
#    def __init__(self):
#        self.volname = ""
#        self.volicon = ""
#        self.window_width  = 500
#        self.window_height = 300
#        self.icon_size     = 96
#        self.icon_name     = None
#        self.icon_xPos     = 0
#        self. ${APP_NAME}.app 135 102 \
#    --hide-extension ${APP_NAME}.app \
#    --app-drop-link 365 102 \


# def makeDmg(bundlePath, dmgPath):
#    create-dmg \
#    --volname "${APP_NAME}" \
#    --volicon "${BUNDLE_RESOURCES_DIR}/${APP_NAME}.icns" \
#    --window-size 500 300 \
#    --icon-size 96 \
#    --icon ${APP_NAME}.app 135 102 \
#    --hide-extension ${APP_NAME}.app \
#    --app-drop-link 365 102 \
#    ${DMG_NAME} \
#    ${APP_NAME}.app

#######################################
#
#######################################
if __name__ == "__main__":
    VERSION = "8.0.0"
    SRC = "flacon-%s.tar.gz" % VERSION
    NAME = "Flacon"
    ARCHITECTURES = ["x86_64", "arm64"]
    #ARCHITECTURES = ["x86_64"]
    BUNDLE_NAME   = f"{NAME}.app"
    THIRD_PARTY_DIR = "third-party"
    DMG_NAME = f"{NAME}_{VERSION}.dmg"
    BUILD_DMG = True

    DEBUG = False

    tmpDir = ".build"
    srcDir   = f"{tmpDir}/src"

    #######################################
    # BUNDLE_PATH     = f"{tmpDir}/x86_64/{BUNDLE_NAME}"
    # checkDyLibs(BUNDLE_PATH)
    # checkArch(BUNDLE_PATH, ARCHITECTURES)
    # sys.exit(1)
    #######################################

    rmdir(tmpDir)
    mkdir(srcDir)
    extract(SRC, srcDir)

    archBundles = []


    # *******************************************
    # ARCH bundles
    for arch in ARCHITECTURES:
        BREW_DIR  = "/opt/homebrew_x86" if arch == "x86_64" else "/opt/homebrew"
        FRAMEWORK_PATH = "/Users/sokoloff/Library/Frameworks"
        BULD_DIR        = f"{tmpDir}/{arch}.build"
        BUNDLE_PATH     = f"{tmpDir}/{arch}/{BUNDLE_NAME}"
        BUNDLE_LIB_PATH = f"{BUNDLE_PATH}/Contents/Frameworks"
        CERT_IDENTITY   = "Developer ID Application: Alex Sokolov (635H9TYSZJ)"

        archBundles.append(BUNDLE_PATH)
        print()

        # prepare ..........................
        mkdir(BULD_DIR)


        # build ............................
        info("Build")
        cmake(
            f"-DMAC_BUNDLE=Yes",
            f"-DCMAKE_INSTALL_PREFIX={BUNDLE_PATH}/..",
            f"-DCMAKE_OSX_DEPLOYMENT_TARGET='10.10.1'",
            f"-DCMAKE_FRAMEWORK_PATH={FRAMEWORK_PATH}",
            f"-DCMAKE_PREFIX_PATH={BREW_DIR}/opt/qt5/lib/cmake;{BREW_DIR}/lib/pkgconfig",
            f"-DPKG_CONFIG_EXECUTABLE={BREW_DIR}/bin/pkg-config",
            f"-DCMAKE_OSX_ARCHITECTURES={arch}",
            f"--log-level=WARNING",
            f"-B{BULD_DIR}",
            srcDir
        )

        make(
            f"-j16",
            f"-C{BULD_DIR}",
        )

        make(
            f"-C{BULD_DIR}",
            f"install",
        )

        # Libraries ........................
        info("Copy third-party binaries and libraries")
        copy(f"{THIRD_PARTY_DIR}/{arch}/", f"{BUNDLE_PATH}/Contents")

        info("Fixup Sparkle")
        call("install_name_tool",
             "-change", "@rpath/Sparkle.framework/Versions/A/Sparkle",
             "@executable_path/../Frameworks/Sparkle.framework/Versions/A/Sparkle",
            f"{BUNDLE_PATH}/Contents/MacOS/Flacon"
        )
        copy(f"{FRAMEWORK_PATH}/Sparkle.framework", f"{BUNDLE_LIB_PATH}/Sparkle.framework")


        # Qt libraries .....................
        info("Fixup Qt libraries")
        call(f"{BREW_DIR}/opt/qt5/bin/macdeployqt",
            f"{BUNDLE_PATH}",
            "-always-overwrite"
        )

        #rmdir(f"/Users/sokoloff/myPrograms/flacon/mac_bundle2/.build/x86_64/Flacon.app/Contents/PlugIns/imageformats

        rmdir(f"{BUNDLE_LIB_PATH}/QtPdf.framework")
        #rmdir(f"{BUNDLE_LIB_PATH}/QtPrintSupport.framework")
        rmdir(f"{BUNDLE_LIB_PATH}/QtQml.framework")
        rmdir(f"{BUNDLE_LIB_PATH}/QtQmlModels.framework")
        rmdir(f"{BUNDLE_LIB_PATH}/QtQuick.framework")
        rmdir(f"{BUNDLE_LIB_PATH}/QtVirtualKeyboard.framework")
        rmdir(f"{BUNDLE_PATH}/Contents/PlugIns/virtualkeyboard")
        rmdir(f"{BUNDLE_PATH}/Contents/PlugIns/printsupport")
        rmfile(f"{BUNDLE_PATH}/Contents/PlugIns/platforminputcontexts/libqtvirtualkeyboardplugin.dylib")
        rmfile(f"{BUNDLE_PATH}/Contents/PlugIns/imageformats/libqpdf.dylib")

        # Check ............................
        info(f"Check libraries for {arch}")
        checkDyLibs(BUNDLE_PATH)



    # *******************************************
    # Universal bundle
    BUNDLE_PATH  = f"./{BUNDLE_NAME}"

    if len(arch) == 1:
        info(f"Creating bundle for {arch[0]}")
    else:
        info("Creating universal bundle")

    call("lipo-app",  *archBundles, BUNDLE_PATH)

    info(f"Check libraries")
    checkDyLibs(BUNDLE_PATH)
    checkArch(BUNDLE_PATH, ARCHITECTURES)

    info("Signing bundle")
    signBundle(BUNDLE_PATH, CERT_IDENTITY)

    if BUILD_DMG:
        call("create-dmg",
            "--volname", f"{NAME}",
            "--volicon", f"{BUNDLE_PATH}/Contents/Resources/{NAME}.icns",
            "--window-size", "500", "300",
            "--icon-size", "96",
            "--icon", f"{BUNDLE_NAME}", "135", "102",
            "--hide-extension", f"{BUNDLE_NAME}",
            "--app-drop-link", "365", "102",
            f"{DMG_NAME}",
            f"{BUNDLE_PATH}"
        )
