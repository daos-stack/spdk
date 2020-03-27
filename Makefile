NAME      := spdk
SRC_EXT   := gz
SOURCE     = https://github.com/spdk/$(NAME)/archive/v$(VERSION).tar.$(SRC_EXT)

PR_REPOS := dpdk@PR-9

#https://github.com/rpm-software-management/mock/issues/384
override MOCK_OPTIONS += --disablerepo=sclo*

include packaging/Makefile_packaging.mk
