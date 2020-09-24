# doesn't seem to work on sles 12.3: #{!?make_build:#define make_build #{__make} #{?_smp_mflags}}
# so...
%if 0%{?suse_version} <= 1320
%define make_build  %{__make} %{?_smp_mflags}
%endif

# Build documentation package
%bcond_with doc

Name: spdk
Version: 20.01.1
Release: 1%{?dist}
Epoch: 0
URL: http://spdk.io

Source: https://github.com/%{name}/%{name}/archive/v%{version}.tar.gz

Patch0: spdk-build-with-installed-dpkg.patch

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
BuildRequires: dpdk-devel = 19.11
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
BuildRequires: python

# Install dependencies
Requires: dpdk = 19.11

Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description
The Storage Performance Development Kit provides a set of tools
and libraries for writing high performance, scalable, user-mode storage
applications.


%package devel
Summary: Storage Performance Development Kit development files
Requires: %{name}%{?_isa} = %{package_version}
Requires: dpdk-devel = 19.11
Provides: %{name}-static%{?_isa} = %{package_version}

%description devel
This package contains the headers and other files needed for
developing applications with the Storage Performance Development Kit.


%package tools
Summary: Storage Performance Development Kit tools files
Requires: %{name}%{?_isa} = %{package_version}
%if (0%{?rhel} >= 7)
%if "%{use_python2}" == "0"
Requires: python3 python3-configshell python3-pexpect
%else
Requires: python python-configshell pexpect
%endif
%else
%if (0%{?suse_version} >= 1500)
Requires: python2-configshell-fb
%else
%if (0%{?suse_version} >= 1315)
Requires: python python-configshell
%endif
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
./configure --prefix=%{_prefix} \
            --disable-tests \
            --with-dpdk=/usr/share/dpdk/x86_64-default-linux-gcc \
            --without-vhost \
            --without-crypto \
            --without-pmdk \
            --without-vpp \
            --without-rbd \
            --with-rdma \
            --with-shared \
            --without-iscsi-initiator \
            --without-isal \
            --without-vtune

%make_build all

%if %{with doc}
make -C doc
%endif

%install
%make_install %{?_smp_mflags} prefix=%{_prefix} libdir=%{_libdir} datadir=%{_datadir}

# Install tools
mkdir -p %{install_datadir}/scripts

## env is banned - replace '/usr/bin/env anything' with '/usr/bin/anything'
#find %{install_datadir}/scripts -type f -regextype egrep -regex '.*([.]py|[.]sh)' \
#       -exec sed -i -E '1s@#!/usr/bin/env (.*)@#!/usr/bin/\1@' {} +

#%if "%{use_python2}" == "1"
#find %{install_datadir}/scripts -type f -regextype egrep -regex '.*([.]py)' \
#       -exec sed -i -E '1s@#!/usr/bin/python3@#!/usr/bin/python2@' {} +
#%endif

# install the setup tool
cp scripts/{setup,common}.sh %{install_datadir}/scripts/
mkdir -p %{install_datadir}/include/spdk/
cp include/spdk/pci_ids.h %{install_datadir}/include/spdk/

%if %{with doc}
# Install doc
mkdir -p %{install_docdir}
mv doc/output/html/ %{install_docdir}
%endif


%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig


%files
%{_bindir}/spdk_*
%dir %{_datadir}/%{name}
%{_libdir}/*.so.*


%files devel
%{_includedir}/%{name}
%{_libdir}/*.a
%{_libdir}/*.so


%files tools
%{_datadir}/%{name}/include
%{_datadir}/%{name}/scripts

%if %{with doc}
%files doc
%{_docdir}/%{name}
%endif


%changelog
* Fri Apr 03 2020 Tom Nabarro <tom.nabarro@intel.com> - 0:20.01.1-1
- Upgrade to enable SPDK via VFIO as non-root w/ CentOS 7.7.
- Remove fio_plugin from build.
- Remove unused cli/rpc tool scripts from build.

* Fri Oct 25 2019 Brian J. Murrell <brian.murrell@intel.com> - 0:19.04.1-1
- New upstream release

* Wed Oct 23 2019 Brian J. Murrell <brian.murrell@intel.com> - 0:18.04-8
- fio-src -> fio-devel

* Wed May 29 2019 Brian J. Murrell <brian.murrell@intel.com> - 0:18.04-7
- tools package needs to have scripts/common.sh and include/spdk/pci_ids.h

* Tue May 07 2019 Brian J. Murrell <brian.murrell@intel.com> - 0:18.04-6
- Support SLES 12.3
  - BuildRequires cunit-devel
  - Use fio-src instead of fio-debuginfo
  - Requires for python-configshell
  - Remove Requires for pexpect because trying to get a pexpect
    package for SLES 12.3 is just ridiculous
  - libiscsi -> libiscsi7
  - libuuid -> libuuid1
  - libaio -> libaio1
  - numactl-libs -> libnuma1
  - openssl-libs -> libopenssl1_0_0
  - librdmacm -> librdmacm1

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
