# doesn't seem to work on sles 12.3: %{!?make_build:%define make_build %{__make} %{?_smp_mflags}}
# so...
%if 0%{?suse_version} <= 1320
%define make_build  %{__make} %{?_smp_mflags}
%endif

# Build documentation package
%bcond_with doc

Name: spdk
Version: 18.04
Release: 6%{?dist}
Epoch: 0
URL: http://spdk.io

Source: https://github.com/spdk/spdk/archive/v%{version}.tar.gz
Patch1: %{name}-051297114.patch

Summary: Set of libraries and utilities for high performance user-mode storage

%define package_version %{epoch}:%{version}-%{release}

%define install_datadir %{buildroot}/%{_datadir}/%{name}
%define install_sbindir %{buildroot}/%{_sbindir}
%define install_docdir %{buildroot}/%{_docdir}/%{name}

# Distros that don't support python3 will use python2
%if "%{dist}" == ".el7"
%define use_python2 1
%else
%define use_python2 0
%endif

License: BSD

# Only x86_64 is supported
ExclusiveArch: x86_64

BuildRequires: gcc gcc-c++ make
# dpdk 18.11 is in "extras" so pin it to our version
BuildRequires: dpdk-devel < 18.11
%if (0%{?rhel} >= 7)
BuildRequires:  numactl-devel
BuildRequires: CUnit-devel
%else
%if (0%{?suse_version} >= 1315)
BuildRequires:  libnuma-devel
BuildRequires: cunit-devel
%endif
%endif
BuildRequires: libiscsi-devel, libaio-devel, openssl-devel, libuuid-devel
BuildRequires: libibverbs-devel, librdmacm-devel
%if %{with doc}
BuildRequires: doxygen mscgen graphviz
%endif
# there is no actual real fio-devel so we've hacked up an fio-src
# to provide /usr/src/fio-3.3 as the stand-in until we can make a proper
# fio-devel, and have spdk actually use it
BuildRequires: fio-src
BuildRequires: python

# Install dependencies
Requires: dpdk = 18.02, numactl-libs, openssl-libs
Requires: libiscsi, libaio, libuuid
# NVMe over Fabrics
Requires: librdmacm, librdmacm
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

# Very hacky workaround to rpmbuild not being able to autoprovides
# for this
Provides: libspdk.so()(64bit)

%description
The Storage Performance Development Kit provides a set of tools
and libraries for writing high performance, scalable, user-mode storage
applications.


%package devel
Summary: Storage Performance Development Kit development files
Requires: %{name}%{?_isa} = %{package_version}
Provides: %{name}-static%{?_isa} = %{package_version}

%description devel
This package contains the headers and other files needed for
developing applications with the Storage Performance Development Kit.


%package tools
Summary: Storage Performance Development Kit tools files
%if (0%{?rhel} >= 7)
%if "%{use_python2}" == "0"
Requires: %{name}%{?_isa} = %{package_version} python3 python3-configshell python3-pexpect
%else
Requires: %{name}%{?_isa} = %{package_version} python python-configshell pexpect
%endif
%else
%if (0%{?suse_version} >= 1315)
Requires: %{name}%{?_isa} = %{package_version} python python-configshell # pexpect
%endif
%endif
BuildArch: noarch

%description tools
%{summary}


%if %{with doc}
%package doc
Summary: Storage Performance Development Kit documentation
BuildArch: noarch

%description doc
%{summary}
%endif


%prep
%autosetup -n spdk-%{version} -p1


%build
./configure --prefix=%{_prefix}                                 \
	--with-dpdk=/usr/share/dpdk/x86_64-default-linuxapp-gcc \
	--with-fio=/usr/src/fio-3.3/
#	--with-fio=/usr
#	--without-fio \
#	--disable-tests \
#	--with-vhost \
#	--without-pmdk \
#	--without-vpp \
#	--without-rbd \
#	--with-rdma \
#	--with-iscsi-initiator \
#	--without-vtune

%make_build all

%if %{with doc}
make -C doc
%endif

%install
%make_install %{?_smp_mflags} prefix=%{_prefix} libdir=%{_libdir} datadir=%{_datadir}

# Install tools
mkdir -p %{install_datadir}
find scripts -type f -regextype egrep -regex '.*(spdkcli|rpc).*[.]py' \
	-exec cp --parents -t %{install_datadir} {} ";"

# env is banned - replace '/usr/bin/env anything' with '/usr/bin/anything'
find %{install_datadir}/scripts -type f -regextype egrep -regex '.*([.]py|[.]sh)' \
	-exec sed -i -E '1s@#!/usr/bin/env (.*)@#!/usr/bin/\1@' {} +

%if "%{use_python2}" == "1"
find %{install_datadir}/scripts -type f -regextype egrep -regex '.*([.]py)' \
	-exec sed -i -E '1s@#!/usr/bin/python3@#!/usr/bin/python2@' {} +
%endif

# synlinks to tools
mkdir -p %{install_sbindir}
ln -sf -r %{install_datadir}/scripts/rpc.py %{install_sbindir}/%{name}-rpc
ln -sf -r %{install_datadir}/scripts/spdkcli.py %{install_sbindir}/%{name}-cli

# Install the fio_plugin
cp examples/nvme/fio_plugin/fio_plugin %{install_datadir}/
# and the setup tool
cp scripts/setup.sh %{install_datadir}/scripts/

%if %{with doc}
# Install doc
mkdir -p %{install_docdir}
mv doc/output/html/ %{install_docdir}
%endif


%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig


%files
%{_bindir}/spdk_*
%{_datadir}/%{name}/fio_plugin
#%{_libdir}/*.so.*
%{_libdir}/*.so


%files devel
%{_includedir}/%{name}
%{_libdir}/*.a


%files tools
%{_datadir}/%{name}/scripts
%{_sbindir}/%{name}-rpc
%{_sbindir}/%{name}-cli

%if %{with doc}
%files doc
%{_docdir}/%{name}
%endif


%changelog
* Fri May 03 2019 Brian J. Murrell <brian.murrell@intel.com> - 0:18.04-6
- SLES 12.3:
  - Requires for python-configshell
  - Remove Requires for pexpect because trying to get a pexpect
    package for SLES 12.3 is just ridiculous

* Fri May 03 2019 Brian J. Murrell <brian.murrell@intel.com> - 0:18.04-5
- Support SLES 12.3
  - BuildRequires cunit-devel
  - Use fio-src instead of fio-debuginfo

* Tue Apr 16 2019 Brian J. Murrell <brian.murrell@intel.com> - 0:18.04-4
- Add hack to pseudo-version shared lib
- Add hack to Provides: libspdk.so()(64bit) until I can figure
  out why the autoprovides is not working

* Fri Apr 05 2019 Brian J. Murrell <brian.murrell@intel.com> - 0:18.04-3
- examples/nvme/fio_plugin needs to go into /usr/share/spdk/
- scripts/setup.sh needs to go into /usr/share/spdk/scripts/
- Requires dpdk = 18.02 to ensure we get the required version
  until we can get our dependencies caught up and in order

* Fri Apr 05 2019 Brian J. Murrell <brian.murrell@intel.com> - 0:18.04-2
- Include examples/nvme/fio_plugin

* Thu Apr 04 2019 Brian J. Murrell <brian.murrell@intel.com> - 0:18.04-1
- Initial RPM release
- Add a patch to catch up from 18.04 to 051297114 until we can advance
  to a newer/actual release of spdk
