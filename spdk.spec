# doesn't seem to work on sles 12.3: #{!?make_build:#define make_build #{__make} #{?_smp_mflags}}
# so...
%if (0%{?suse_version} <= 1320)
%define make_build  %{__make} %{?_smp_mflags}
%endif

%{!?libdir:%define libdir /usr/local/lib}

%define debug_package %{nil}
%global _hardened_build 1
%global __python %{__python3}


# Build documentation package
%bcond_with doc

Name:     spdk
Version:  24.09
Release:  1%{?dist}
Epoch:    0

Summary:  Set of libraries and utilities for high performance user-mode storage

License:  BSD
URL:      http://spdk.io
Source0:  %{name}-%{version}.tar.gz

%define package_version %{epoch}:%{version}-%{release}

%define install_datadir %{buildroot}/%{_datadir}/%{name}
%define install_docdir %{buildroot}/%{_docdir}/%{name}

# Distros that don't support python3 will use python2
%if "%{dist}" == ".el7" || (0%{?suse_version} > 0 && 9999999%{?sle_version} < 150400)
%define use_python2 1
%else
%define use_python3 1
%endif

# Only x86_64 is supported
ExclusiveArch: x86_64

BuildRequires: kernel-headers
BuildRequires: gcc gcc-c++ make
%if (0%{?rhel} >= 7)
BuildRequires: numactl-devel
%else
%if (0%{?suse_version} >= 1315)
BuildRequires: libnuma-devel
%endif
%endif
BuildRequires: libaio-devel, openssl-devel, libuuid-devel
%if (0%{?rhel} >= 8) && (0%{?rhel} < 9)
BuildRequires: python36
%else
BuildRequires: python
%endif
BuildRequires: meson

BuildRequires: python3-pyelftools
BuildRequires: python3-pip
BuildRequires: patchelf

Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description
The Storage Performance Development Kit provides a set of tools
and libraries for writing high performance, scalable, user-mode storage
applications.


%package devel
Summary: Storage Performance Development Kit development files

%description devel
This package contains the headers and other files needed for
developing applications with the Storage Performance Development Kit.


%package tools
Summary: Storage Performance Development Kit tools files
Requires: %{name}%{?_isa} = %{package_version}
%if (0%{?rhel} >= 7)
%if 0%{?use_python3}
Requires: python3 python3-configshell python3-pexpect
%else
Requires: python python-configshell pexpect
%endif
%else
%if (0%{?suse_version} >= 1500)
%if 0%{?use_python2}
Requires: python2-configshell-fb
%endif
%if 0%{?use_python3}
Requires: python3-configshell-fb
%endif
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


%if (0%{?suse_version} > 0)
%global __debug_package 1
%global _debuginfo_subpackages 0
%debug_package
%endif

%prep
%autosetup -n %{name}-%{version} -p1

# Workaround for https://github.com/spdk/spdk/issue/2531
sed -i -e 's/\(-L\$1\/\)lib/\1%{_lib}/' scripts/pc.sh

# Resolve rpath errors in leap15 rpmlint.
sed -i -e '/-Wl,-rpath=\$(DESTDIR)\/\$(libdir)/d' mk/spdk.common.mk

%build

%if (0%{?suse_version} > 0)
export CFLAGS="%{optflags} -fPIC -pie"
export CXXFLAGS="%{optflags} -fPIC -pie"
# this results in compiler errors, so we are unable to produce PIEs on Leap15
#export LDFLAGS="$LDFLAGS -pie"
%else
export CFLAGS="${CFLAGS:-%optflags}"
export CXXFLAGS="${CXXFLAGS:-%optflags}"
export FFLAGS="${FFLAGS:-%optflags}"
%if "%{?build_ldflags}" != ""
export LDFLAGS="${LDFLAGS:-%{build_ldflags}}"
%endif
%endif
alias pip=pip3
./configure                           \
            --prefix=%{_prefix}       \
%if (0%{?rhel} && 0%{?rhel} < 8)
            --target-arch=core-avx2   \
%else
            --target-arch=haswell     \
%endif
            --disable-tests           \
            --disable-unit-tests      \
            --disable-apps            \
            --without-vhost           \
            --without-crypto          \
            --without-rbd             \
            --without-iscsi-initiator \
            --without-vtune           \
            --without-nvme-cuse       \
            --without-raid5f          \
            --without-avahi          \
            --without-usdt          \
            --without-wpdk          \
            --with-shared
%make_build all

%if %{with doc}
make -C doc
%endif


%install
alias pip=pip3
%make_install %{?_smp_mflags} prefix=%{_prefix} libdir=%{_libdir} datadir=%{_datadir}

# Remove some dpdk stuff we don't need
rm -f %{buildroot}/usr/bin/dpdk-*.py
rm -rf %{buildroot}/usr/share/dpdk
rm -rf %{buildroot}/usr/share/doc/dpdk
mv %{buildroot}/usr/lib/python* %{buildroot}/%{_libdir}
chmod o+x %{buildroot}/%{_libdir}/python*/*/spdk/sma/qmp.py
mv %{buildroot}/usr/lib %{buildroot}/%{_libdir}/spdk
mkdir -p %{buildroot}/etc
mkdir -p %{buildroot}/etc/ld.so.conf.d
cat <<-EOF > %{buildroot}/etc/ld.so.conf.d/spdk.conf
%{_libdir}/spdk
EOF
rm -rf %{buildroot}/%{_libdir}/pkgconfig/*
cat <<-EOF > %{buildroot}/%{_libdir}/pkgconfig/spdk.pc
Description: SPDK General
Version: %{version}
Name: spdk
Libs: -L%{_libdir}/spdk
EOF

# Install tools
mkdir -p %{install_datadir}/scripts

# Install the setup tool
cp scripts/{setup,common}.sh %{install_datadir}/scripts/
mkdir -p %{install_datadir}/include/%{name}/
cp include/%{name}/pci_ids.h %{install_datadir}/include/%{name}/
# spdk_nvme_identify and spdk_nvme_perf are already installed by default
strip -s build/examples/lsvmd
patchelf --remove-rpath build/examples/lsvmd
strip -s build/examples/nvme_manage
patchelf --remove-rpath build/examples/nvme_manage
cp build/examples/lsvmd %{buildroot}/%{_bindir}/spdk_nvme_lsvmd
cp build/examples/nvme_manage %{buildroot}/%{_bindir}/spdk_nvme_manage
strip -s %{buildroot}/%{_libdir}/*.so.*.* || true
strip -s %{buildroot}/%{_libdir}/spdk/*.so.*.* || true
strip -s %{buildroot}/%{_libdir}/spdk/*/*.so.*.* || true


# Install rpc.py tool
cp scripts/rpc.py %{install_datadir}/scripts/

# Change /usr/bin/{env ,}bash/python to resolve env-script-interpreter rpmlint error.
sed -i -e '1s/env //' %{install_datadir}/scripts/{setup.sh,rpc.py}

%if %{with doc}
# Install doc
mkdir -p %{install_docdir}
mv doc/output/html/ %{install_docdir}
%endif

# Remove unused static libs
rm -f %{buildroot}/%{_libdir}/*.a

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig


%files
%dir %{_datadir}/%{name}
%{_libdir}/*.so.*
%{_bindir}/*
%{_libdir}/spdk/*.so.*
%{_libdir}/python*/*
/etc/ld.so.conf.d/spdk.conf
%{_libdir}/spdk/dpdk/pmds*/*.so.*


%files devel
%{_includedir}/*
%{_libdir}/*.so
%{_libdir}/pkgconfig
%{_libdir}/spdk/*.a
%{_libdir}/spdk/*.so
%{_libdir}/spdk/dpdk/pmds*/*.so
%{_libdir}/spdk/pkgconfig

%files tools
%{_datadir}/%{name}/include
%{_datadir}/%{name}/scripts

%if %{with doc}
%files doc
%{_docdir}/%{name}
%endif


%changelog
* Tue Mar 11 2025 Jeff Olivier <jeffolivier@google.com> - 0:24.09-1
- Upgrade to SPDK 24.09. Use source snapshot and deprecate separate dpdk RPM

* Tue Apr 23 2024 Tomasz Gromadzki <tomasz.gromadzki@intel.com> - 0:22.01.2-6
- Add rpc.py to spdk-tools package.

* Mon Oct 16 2023 Brian J. Murrell <brian.murrell@intel.com> - 0:22.01.2-5
- Change spdk-devel's R: dpdk-devel to dpdk-daos-devel to ensure we get the
  daos-targetted dpdk build

* Thu Jun 22 2023 Brian J. Murrell <brian.murrell@intel.com> - 0:22.01.2-4
- Build on EL9
- Change BR: dpdk-devel to dpdk-daos-devel to ensure we get the
  daos-targetted dpdk build
- Target core-avx2 instruction set on EL7 and haswell on everything else

* Tue Jan 10 2023 Tom Nabarro <tom.nabarro@intel.com> - 0:22.01.2-3
- Add patch to fix build with glib 2.3.

* Sun Nov 27 2022 Brian J. Murrell <brian.murrell@intel.com> - 0:22.01.2-2
- Build on Leap 15.4 build
  - Leap 15.4 drops much python2 support

* Thu Nov 24 2022 Tom Nabarro <tom.nabarro@intel.com> - 0:22.01.2-1
- Upgrade SPDK to 22.01.2 maintenance release (VMD-hotplug fixes).
- Update DPDK dependency version to 21.11.2 (CVE fix).

* Wed Nov 09 2022 Tom Nabarro <tom.nabarro@intel.com> - 0:22.01.1-3
- Remove unnecessary --with-rdma configure option.

* Thu Jul 28 2022 Tom Nabarro <tom.nabarro@intel.com> - 0:22.01.1-2
- Add back a patch referenced by previous DAOS release.

* Tue May 17 2022 Tom Nabarro <tom.nabarro@intel.com> - 0:22.01.1-1
- Upgrade SPDK to 22.01.1 LTS release.
- Update DPDK dependency version to 21.11.1.

* Fri Apr 08 2022 Tom Nabarro <tom.nabarro@intel.com> - 0:21.07-16
- Add patch to fix bug in previous fix for VMD init after reboot.
- Squash patches to workaround DAOS-10291 bug.

* Sun Apr 03 2022 Tom Nabarro <tom.nabarro@intel.com> - 0:21.07-15
- Add patch to improve driver rebinding times when VMD is enabled.

* Wed Mar 23 2022 Tom Nabarro <tom.nabarro@intel.com> - 0:21.07-14
- Add (again) patches to fix error on VMD init after reboot.

* Tue Mar 15 2022 Michael MacDonald <mjmac.macdonald@intel.com> - 0:21.07-13
- Revert landing of SPDK fixes for VMD.

* Wed Mar 09 2022 Tom Nabarro <tom.nabarro@intel.com> - 0:21.07-12
- Add patches to fix error on VMD init after reboot.

* Fri Jan 28 2022 Jeff Olivier <jeffrey.v.olivier@intel.com> - 0:21.07-11
- Rename spdk example app binaries to be consistent with those existing.

* Sat Jan 01 2022 Tom Nabarro <tom.nabarro@intel.com> - 0:21.07-10
- Add nvme_manage example app to binary directory.

* Tue Dec 14 2021 Tom Nabarro <tom.nabarro@intel.com> - 0:21.07-9
- Add patch to add uint8 JSON decode function.

* Fri Nov 26 2021 Tom Nabarro <tom.nabarro@intel.com> - 0:21.07-8
- Add patch to fix printing of correct socket-ID for VMD backing
  devices.

* Tue Nov 09 2021 Tom Nabarro <tom.nabarro@intel.com> - 0:21.07-7
- Add patch to enable use of PCI event module with non-root process.

* Wed Oct 20 2021 Saurabh Tandan <saurabh.tandan@intel.com> - 0:21.07-6
- Adding lsvmd to the binary dir

* Mon Oct 11 2021 Sydney Vanda <sydney.m.vanda@intel.com> - 0:21.07-5
- Add patch for performance degradation after repeated format.

* Tue Sep 07 2021 Tom Nabarro <tom.nabarro@intel.com> - 0:21.07-4
- Add patch for ICX VMD driver update.

* Fri Aug 13 2021 John Malmberg <john.e.malmberg@intel.com> - 0:21.07-3
- Require dpdk >= 21.05

* Tue Aug 10 2021 Tom Nabarro <tom.nabarro@intel.com> - 0:21.07-2
- Add patch to enable multiple dpdk cli opts on init.

* Tue Aug 03 2021 Tom Nabarro <tom.nabarro@intel.com> - 0:21.07-1
- Upgrade SPDK to 21.07 release.

* Tue Jul 20 2021 Tom Nabarro <tom.nabarro@intel.com> - 0:21.04-2
- Add example binaries to main package.

* Tue Jun 29 2021 Tom Nabarro <tom.nabarro@intel.com> - 0:21.04-1
- Upgrade SPDK to 21.04 + patch to custom githash on 21.07-pre
- BR: dpdk-devel and R: dpdk = 21.05
- Set bare --with-dpdk in configure to use libdpdk.pc

* Thu Jun 03 2021 Johann Lombardi <johann.lombardi@intel.com> - 0:20.01.2-2
- Remove Get Num Queues initialization step

* Thu Feb 11 2021 Brian J. Murrell <brian.murrell@intel.com> - 0:20.01.2-1
- Update to 20.01.2
- BR: dpdk-devel and R: dpdk = 19.11.6

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
