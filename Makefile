NAME      := spdk
SRC_EXT   := gz
SOURCE     = https://github.com/spdk/$(NAME)/archive/v$(VERSION).tar.$(SRC_EXT)

#https://github.com/rpm-software-management/mock/issues/384
override MOCK_OPTIONS += --disablerepo=sclo*

include packaging/Makefile_packaging.mk
