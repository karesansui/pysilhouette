%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%define name    pysilhouette
%define version 0.8.2
%define release 1

%define __python        $(which python)
%define __chkconfig     /sbin/chkconfig
%define __app           pysilhouette
%define __prog          silhouette
%define __progd         %{__prog}d

%define _psi_sysconfdir %{_sysconfdir}/%{__app}
%define _psi_bindir     %{_bindir}
%define _psi_datadir    %{_localstatedir}/lib/%{__app}

%define _user           pysilhouette
%define _group          pysilhouette
%define _uid_min        300
%define _uid_max        350

Summary:         A python-based background job manager
Summary(ja):    オープンソースバックグラウンドジョブマネージャー
Name:           %{name}
Version:        %{version}
Release:        %{release}
License:        MIT/X11
Group:          System Environment/Daemons
Vendor:         Karesansui Project
URL:            http://sourceforge.jp/projects/pysilhouette/
Packager:       Taizo ITO <taizo@karesansui-project.info>
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix:         %{_prefix}
BuildArch:      noarch
BuildRequires:  python-setuptools

%description
Pysilhouette is a python-based background job manager,
intended to co-work with various python-based web applications.
It makes it available to get job status to programmers,
which was difficult in http-based stateless/interactive session before.
100% Pure Python.

%prep
%setup

%build
python setup.py build

%install
python setup.py install --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

mkdir -p $RPM_BUILD_ROOT%{_psi_sysconfdir}
mkdir -p $RPM_BUILD_ROOT%{_psi_bindir}
mkdir -p $RPM_BUILD_ROOT%{_initrddir}/
mkdir -p $RPM_BUILD_ROOT/etc/sysconfig
mkdir -p $RPM_BUILD_ROOT/var/log/%{__app}/
mkdir -p $RPM_BUILD_ROOT%{_psi_datadir}

pushd sample
install -c -m 644 log.conf.example $RPM_BUILD_ROOT%{_psi_sysconfdir}/log.conf.example
install -c -m 644 log.conf.example $RPM_BUILD_ROOT%{_psi_sysconfdir}/log.conf

install -c -m 644 %{__prog}.conf.example $RPM_BUILD_ROOT%{_psi_sysconfdir}/%{__prog}.conf.example
install -c -m 644 %{__prog}.conf.example $RPM_BUILD_ROOT%{_psi_sysconfdir}/%{__prog}.conf

install -c -m 644 whitelist.conf.example $RPM_BUILD_ROOT%{_psi_sysconfdir}/whitelist.conf.example
install -c -m 644 whitelist.conf.example $RPM_BUILD_ROOT%{_psi_sysconfdir}/whitelist.conf

install -c -m 644 rc.d/init.d/* $RPM_BUILD_ROOT%{_initrddir}/
install -c -m 644 sysconfig/%{__progd} $RPM_BUILD_ROOT/etc/sysconfig/%{__progd}
popd

install -c -m 744 tools/psil-cleandb $RPM_BUILD_ROOT%{_psi_bindir}
install -c -m 744 tools/psil-set $RPM_BUILD_ROOT%{_psi_bindir}

chmod +x %{__app}/%{__prog}.py

%clean
rm -rf $RPM_BUILD_ROOT

%pre
# Add group
getent group | %{__grep} "^%{_group}:" >/dev/null 2>&1
if [ $? -ne 0 ]; then
  __uid=%{_uid_min}
  while test ${__uid} -le %{_uid_max}
  do
    getent group | %{__grep} "^[^:]*:x:${__uid}:" >/dev/null 2>&1
    if [ $? -ne 0 ]; then
      _gid=${__uid}
      break
    fi
    __uid=`expr ${__uid} + 1`
  done
  /usr/sbin/groupadd -g ${_gid} -f %{_group}
fi

# Add user
getent passwd | %{__grep} "^%{_user}:" >/dev/null 2>&1
if [ $? -ne 0 ]; then
  __uid=%{_uid_min}
  while test ${__uid} -le %{_uid_max}
  do
    getent passwd | %{__grep} "^[^:]*:x:${__uid}:" >/dev/null 2>&1
    if [ $? -ne 0 ]; then
      _uid=${__uid}
      break
    fi
    __uid=`expr ${__uid} + 1`
  done
  /usr/sbin/useradd -c "Pysilhouette Job Manager" -u ${_uid} -g %{_group} -d %{_psi_datadir} -s /bin/false -r %{_user} 2> /dev/null || :
fi

%post
#echo "%{__ln_s} %{python_sitelib}/%{__app}/%{__prog}.py %{_psi_bindir}"
%{__ln_s} %{python_sitelib}/%{__app}/%{__prog}.py %{_psi_bindir}
if [ ! -e %{_psi_datadir} ]; then
  mkdir -p %{_psi_datadir} 2> /dev/null
fi
%{__chkconfig} --add silhouetted >/dev/null 2>&1
%{__chkconfig} silhouetted on >/dev/null 2>&1
#%{_initrddir}/silhouetted start >/dev/null 2>&1

%postun
rm -f %{_psi_bindir}/%{__prog}.py
if [ $1 = 0 ]; then
  /usr/sbin/userdel %{_user} 2> /dev/null || :
  /usr/sbin/groupdel %{_group} 2> /dev/null || :
fi
#%{_initrddir}/silhouetted stop >/dev/null 2>&1
#%{__chkconfig} --del silhouetted >/dev/null 2>&1

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc doc tools MANIFEST.in LICENSE sample AUTHORS ChangeLog INSTALL INSTALL.ja README README.ja setup.cfg setup.py debian
%dir %attr(0755, root, root) %{_psi_sysconfdir}
%attr(0755, root, root) %{_initrddir}/*
%attr(0644, root, root) %config(noreplace) %{_psi_sysconfdir}/log.conf
%attr(0644, root, root) %{_psi_sysconfdir}/log.conf.example
%attr(0644, root, root) %config(noreplace) %{_psi_sysconfdir}/%{__prog}.conf
%attr(0644, root, root) %{_psi_sysconfdir}/%{__prog}.conf.example
%attr(0644, root, root) %config(noreplace) %{_psi_sysconfdir}/whitelist.conf
%attr(0644, root, root) %{_psi_sysconfdir}/whitelist.conf.example
%attr(0644, root, root) %config(noreplace) /etc/sysconfig/%{__progd}
#%{_psi_bindir}/%{__prog}.py
%{_psi_bindir}/psil-cleandb
%{_psi_bindir}/psil-set
%dir /var/log/%{__app}
%dir %{_psi_datadir}

%changelog
* Thu Sep 13 2012 Taizo ITO <taizo@karesansui-project.info> - 0.8.2-1
- 0.8.2 released.

* Tue Jul 31 2012 Taizo ITO <taizo@karesansui-project.info> - 0.8.1-2
- Add python-setuptools to BuildRequires tag.

* Wed Jun 20 2012 Taizo ITO <taizo@karesansui-project.info> - 0.8.1-1
- 0.8.1 released.
- Allow to parse command arguments included spaces.

* Mon Apr  2 2012 Taizo ITO <taizo@karesansui-project.info> - 0.8.0-1
- 0.8.0 released.

* Fri Jul 29 2010 Kei Funagayama <kei.topaz@gmail.com> - 0.7.0-1
- 0.7.0 released.

* Tue Jun 29 2010 Kei Funagayama <kei.topaz@gmail.com> - 0.7.0-1beta3
- 0.7.0 beta3 released.

* Fri Apr 09 2010 Kei Funagayama <kei.topaz@gmail.com> - 0.7.0-1beta2
- 0.7.0 beta2 released.

* Fri Apr 09 2010 Kei Funagayama <kei.topaz@gmail.com> - 0.7.0-1beta1
- 0.7.0 beta1 released.

* Wed Jan 03 2010 Kei Funagayama <kei@karesansui-project.info> - 0.7.0-1alpha1
- 0.7.0 alpha1 released.

* Tue Aug 04 2009 Kei Funagayama <kei@karesansui-project.info> - 0.6.3-1
- Add Command Tools.
- Add Debian packaging.

* Fri Jul 24 2009 Kei Funagayama <kei@karesansui-project.info> - 0.6.2-2
- Add documentation.

* Tue Jun 16 2009 Kei Funagayama <kei@karesansui-project.info> - 0.6.2-1
- Add Database copy command.
- SQLite time to register with the system, had not added the time zone information.

* Tue May 19 2009 Taizo ITO <taizo@karesansui-project.info> - 0.6.1-1
- Initial build.
