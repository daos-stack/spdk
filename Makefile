NAME    := spdk
SRC_EXT := gz
SOURCE   = https://github.com/spdk/$(NAME)/archive/v$(VERSION).tar.$(SRC_EXT)

GIT_COMMIT := 7232c450f97cf925a521a60ef2561eca4b65c41a

# this needs to be formalized into packaging/Makefile_packaging.mk
BUILD_DEFINES := --define "commit $(GIT_COMMIT)"
RPM_BUILD_OPTIONS := $(BUILD_DEFINES)

#https://github.com/rpm-software-management/mock/issues/384
override MOCK_OPTIONS += --disablerepo=sclo*

include packaging/Makefile_packaging.mk

# This not really intended to run in CI.  It's meant as a developer
# convenience to generate the needed patch and add it to the repo to
# be committed.
# Should figure out a way to formalize this into
# packaging/Makefile_packaging.mk
$(VERSION)..$(GIT_COMMIT).patch:
	# it really sucks that GitHub's "compare" returns such dirty patches
	#curl -O 'https://github.com/hpc/$(NAME)/compare/$@'
	git clone git@github.com:spdk/$(NAME).git
	pushd $(NAME) &&                                \
	trap 'popd && rm -rf $(NAME)' EXIT;             \
	git diff $(VERSION)..$(GIT_COMMIT) --stat       \
	git diff $(VERSION)..$(GIT_COMMIT)              \
	    > ../$@
	git add $@
