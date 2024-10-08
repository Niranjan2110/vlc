# LIBARCHIVE
LIBARCHIVE_VERSION := 3.7.6
LIBARCHIVE_URL := http://www.libarchive.org/downloads/libarchive-$(LIBARCHIVE_VERSION).tar.gz

PKGS += libarchive
ifeq ($(call need_pkg,"libarchive >= 3.2.0"),)
PKGS_FOUND += libarchive
endif

DEPS_libarchive = zlib $(DEPS_zlib)
ifdef HAVE_WINSTORE
# libarchive uses CreateHardLinkW
DEPS_libarchive += alloweduwp $(DEPS_alloweduwp)
endif

LIBARCHIVE_CONF := \
		-DENABLE_CPIO=OFF -DENABLE_TAR=OFF -DENABLE_CAT=OFF \
		-DENABLE_NETTLE=OFF \
		-DENABLE_LIBXML2=OFF -DENABLE_LZMA=OFF -DENABLE_ICONV=OFF -DENABLE_EXPAT=OFF \
		-DENABLE_TEST=OFF

# CNG enables bcrypt on Windows and useless otherwise, it's not used when building for XP
LIBARCHIVE_CONF +=-DENABLE_CNG=ON

# bsdunzip doesn't build on macos, android and emscripten and it's disabled on Windows
LIBARCHIVE_CONF +=-DENABLE_UNZIP=OFF

ifdef HAVE_WIN32
LIBARCHIVE_CONF += -DENABLE_OPENSSL=OFF
endif

ifdef HAVE_MACOSX
# these functions are detected as present but there are not until macOS 10.10
# the minimum supported value is 10.7, in each case missing the functions falls
# back to an alternative
LIBARCHIVE_CONF += -DHAVE_FDOPENDIR:INTERNAL= -DHAVE_OPENAT:INTERNAL= -DHAVE_FSTATAT:INTERNAL= -DHAVE_LINKAT:INTERNAL=
endif

$(TARBALLS)/libarchive-$(LIBARCHIVE_VERSION).tar.gz:
	$(call download_pkg,$(LIBARCHIVE_URL),libarchive)

.sum-libarchive: libarchive-$(LIBARCHIVE_VERSION).tar.gz

libarchive: libarchive-$(LIBARCHIVE_VERSION).tar.gz .sum-libarchive
	$(UNPACK)
	$(APPLY) $(SRC)/libarchive/0001-zstd-use-GetNativeSystemInfo-to-get-the-number-of-th.patch
	$(call pkg_static,"build/pkgconfig/libarchive.pc.in")
	$(MOVE)

.libarchive: libarchive toolchain.cmake
	$(CMAKECLEAN)
	$(HOSTVARS) $(CMAKE) $(LIBARCHIVE_CONF)
	+$(CMAKEBUILD)
	$(CMAKEINSTALL)
	touch $@
