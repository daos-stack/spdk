NAME    := spdk
SRC_EXT := gz
SOURCE   = https://github.com/spdk/$(NAME)/archive/v$(VERSION).tar.$(SRC_EXT)
ID_LIKE := $(shell . /etc/os-release; echo $$ID_LIKE)
PATCHES := $(NAME)-051297114.patch

ifeq ($(ID_LIKE),debian)
GIT_DESCRIBE := v18.04-634-g0512971
SOURCE := https://github.com/spdk/spdk/archive/$(GIT_DESCRIBE).tar.$(SRC_EXT)
UBUNTU_ARCHIVE := http://archive.ubuntu.com/ubuntu/pool/universe
FIO_VERSION := 3.8
FIO_SOURCE1 := $(UBUNTU_ARCHIVE)/f/fio/fio_$(FIO_VERSION).orig.tar.gz
FIO_SOURCE2 := $(UBUNTU_ARCHIVE)/f/fio/fio_$(FIO_VERSION)-1.debian.tar.xz
PATCHES := $(shell rm -f fio_source.patch) fio_source.patch
DEB_TOP := _topdir/BUILD

$(notdir $(SOURCE)):
	curl -f -L -O '$(SOURCE)'
	#ln -f $@ v$(VERSION).tar.$(SRC_EXT)

$(notdir $(FIO_SOURCE1)):
	curl -f -L -O '$(FIO_SOURCE1)'

$(notdir $(FIO_SOURCE2)):
	curl -f -L -O '$(FIO_SOURCE2)'

fio_source.patch: $(DEB_TOP)/fio
	touch $@

$(DEB_TOP)/fio: $(notdir $(FIO_SOURCE1)) $(notdir $(FIO_SOURCE2)) | $(DEB_TOP)/
	rm -rf ./$(DEB_TOP)/fio
	mkdir -p $(DEB_TOP)/fio
	tar -C $(DEB_TOP)/fio --strip-components=1 -xf $(notdir $(FIO_SOURCE1))
	tar -C $(DEB_TOP)/fio -xf $(notdir $(FIO_SOURCE2))
	cd $(DEB_TOP)/fio; \
	  export QUILT_PATCHES=debian/patches; \
	  export QUILT_REFRESH_ARGS="-p ab --no-timestamps --no-index";\
	  quilt push -a;
	cd $(DEB_TOP)/fio; ./configure
endif

include Makefile_packaging.mk

