#
# spec file for package python-pysilhouette 
#
# Copyright (c) 2012 SUSE LINUX Products GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#

%define pyname pysilhouette
%define grp psil
%define usr psil

%define ap_docroot /srv/www/htdocs

Name:           python-pysilhouette
Version:        0.8.2
Release:        0
License:        MIT
Summary:        A 100% pure Python daemon
Url:            https://github.com/karesansui/pysilhouette
Group:          Development/Languages/Python
Source0:        %{pyname}-0.8.2.tar.gz
Source1:        %{pyname}.sysconfig
Source2:        %{pyname}.init
Patch0:         %{pyname}-conf.patch
Patch1:         %{pyname}-doc.patch
%if 0%{?suse_version} >= 1140
BuildArch:      noarch
%endif
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildRequires:  fdupes
BuildRequires:  python-devel
BuildRequires:  python-setuptools
Requires:       python-SQLAlchemy
Requires:       python-web.py
%{py_requires}

%description
Pysilhouette is a 100% pure Python daemon which executes background
job commands queued in database.
By default SQLite3 is used as DB.

%package doc
Summary:        PySilhuoette html doc
Group:          Documentation/Other
Requires:       epydoc
Requires:       graphviz-doc
Requires:       graphviz-gd
Requires:       python-SQLAlchemy

%description doc
This package contains PySilhouettes html documentation.

%prep
%setup -q -n %{pyname}-%{version}
%patch0
%patch1
## rpmlint
# non-executable-script (remove shebang)
pushd %{pyname}
find -name "*.py" -exec sed -i -e '/^#\!/d' {} \;
popd
# spurious-executable-perm
chmod 644 sample/scritps/* sample/rc.d/init.d/* tools/*

%build
python setup.py build

%install
python setup.py install --prefix=%{_prefix} --root=%{buildroot}

# install needed dirs
%{__install} -d %{buildroot}%{_sbindir}
%{__install} -d %{buildroot}%{_localstatedir}/{lib,log}/%{pyname}
%{__install} -D -m0644 %{S:1} %{buildroot}%{_localstatedir}/adm/fillup-templates/sysconfig.%{pyname}

# install init script
%{__install} -D -m0755 %{S:2} %{buildroot}/etc/init.d/%{pyname}
%{__ln_s} -f ../../etc/init.d/%{pyname} %{buildroot}%{_sbindir}/rc%{pyname}

# install binaries
%{__install} -D -m0755 tools/psil-cleandb %{buildroot}%{_bindir}/psil-cleandb
%{__install} -D -m0755 tools/psil-set %{buildroot}%{_bindir}/psil-set

# create symlink for silhouette.py
%{__ln_s} -f ../..%{python_sitelib}/%{pyname}/silhouette.py %{buildroot}%{_bindir}/%{pyname}

# prepare silhouette.conf.example
sed -i -e "s,@python_sitelib@,%{python_sitelib}," sample/silhouette.conf.example

# install confs
%{__install} -D -m0644 sample/log.conf.example %{buildroot}%{_sysconfdir}/%{pyname}/log.conf
%{__install} -D -m0644 sample/silhouette.conf.example %{buildroot}%{_sysconfdir}/%{pyname}/pysilhouette.conf
[ -s sample/whitelist.conf.example ] || echo "#" >> sample/whitelist.conf.example ;
%{__install} -D -m0644 sample/whitelist.conf.example %{buildroot}%{_sysconfdir}/%{pyname}/whitelist.conf

### generate/prep doc
sed -i -e "s,@py_dir@,%{py_prefix}/%{_lib}/python,g" \
  -e "s,@python_sitelib@,%{python_sitelib},g" \
  -e "s,@docdir@,%{_docdir},g" \
  -e "s,@ap_docroot@,%{ap_docroot},g" \
 tools/epydoc.sh
sed -i -e "s,^target:.*,target: %{ap_docroot}/%{pyname}-doc," doc/epydoc.cfg
#export PYTHONPATH=${PYTHONPATH}:%{py_prefix}/%{_lib}/python:%{py_libdir}:%{python_sitelib}
#target=%{pyname}-doc
#[ -e ${target} ] && rm -rf ${target} ;
#install -d ${target}
#epydoc -v --config doc/epydoc.cfg

## rpmlint
# files-duplicate
%fdupes %{buildroot}%{python_sitelib}/*

%pre
%{_sbindir}/groupadd -r %{grp} 2>/dev/null || :
%{_sbindir}/useradd -c "PySilhouette Job Manager" -d %{_localstatedir}/lib/%{pyname} \
 -G %{grp} -g %{grp} -r -s /bin/bash %{usr} 2>/dev/null || :

%preun
%stop_on_removal %{pyname}

%post
%{fillup_and_insserv %{pyname}}
# prepare sample/silhouette.conf.example (@uniqkey@)
sed -i -e "s,^env.uniqkey=@uniqkey@,env.uniqkey=`/usr/bin/uuidgen`," \
 %{_sysconfdir}/%{pyname}/pysilhouette.conf

%postun
%restart_on_update %{pyname}
%insserv_cleanup

%files
%defattr(-,root,root)
%doc AUTHORS ChangeLog LICENSE README*
%doc sample/scritps tools/sqlite2other.py
%dir %{_sysconfdir}/%{pyname}
%config(noreplace) %{_sysconfdir}/%{pyname}/log.conf
%config(noreplace) %{_sysconfdir}/%{pyname}/pysilhouette.conf
%config(noreplace) %{_sysconfdir}/%{pyname}/whitelist.conf
%{_sysconfdir}/init.d/%{pyname}
%{_bindir}/psil-cleandb
%{_bindir}/psil-set
%{_bindir}/%{pyname}
%{_sbindir}/rc%{pyname}
%{python_sitelib}/*
%{_localstatedir}/adm/fillup-templates/sysconfig.%{pyname}
%attr(750,psil,root) %{_localstatedir}/lib/%{pyname}
%attr(750,psil,root) %{_localstatedir}/log/%{pyname}

%files doc
%defattr(-,root,root)
#doc %{pyname}-doc/*
%doc doc/epydoc.cfg tools/epydoc.sh

%changelog

