#!/bin/bash

echo "Checking the environment..."
unameOut="$(uname -s)"
case "${unameOut}" in
	Linux*)     machine=linux;;
	Darwin*)    machine=mac;;
	CYGWIN*)    machine=cygwin;;
	MSYS*)      machine=msys;;
	MINGW32*)   machine=mingw32;;
	MINGW64*)   machine=mingw64;;
	*)          machine=unknown;;
esac
if [ "${machine}" = "unknown" ] ; then
	echo "* Warning! Unknown environment: ${unameOut}"
else
	echo "* ${machine} environment detected!"
fi

# $1 = url $2 = dst
function download_url {
	url=$1
	dst=$2
	# check if wget or curl is installed
	if [ -x "$(command -v wget)" ] ; then
		echo "Downloading apt-cyg using wget..."
		wget $url -O $dst
	elif [ -x "$(command -v curl)" ]; then
		echo "Downloading apt-cyg using curl..."
		curl -o $dst -sfL $url
	else
		echo "Could not find curl or wget! Cannot download and install a package manager!" >&2
		exit 1
	fi
}

# $1 = package_name
function install_package {
	# check if the installer (package manager) exists
	if [ "${machine}" = "cygwin" ] ; then
		while true; do
			if [ ! -x "$(command -v apt-cyg --version)" ] ; then
				# we give it one more chance and try to download the installer
				echo "Do you want to download the cygwin package manager (apt-cyg) and install the required utilities? (Press 1 or 2)"
				select yn in "Yes" "No"; do
					case $yn in
						Yes )
							url="rawgit.com/transcode-open/apt-cyg/master/apt-cyg"
							dst="/tmp/apt-cyg"
							download_url $url $dst
							install $dst /bin
							rm $dst
							break;;
						No ) 
							echo "Please install it manually using you package manager!" >&2
							exit 1;
					esac
				done
			else
				break
			fi
		done
	elif [ "${machine}" = "msys" ] ; then
		if [ ! -x "$(command -v pacman)" ] ; then
			echo "Cannot detect pacman manager. Please install it manually using you package manager!" >&2
			exit 1;
		fi
	fi

	# now install
	echo "Do you want to install '$1' now? (Press 1 or 2)"
	select yn in "Yes" "No"; do
		case $yn in
			Yes )
				break;;
			No ) 
				echo "Please install it manually using your package manager!" >&2
				exit 1;
		esac
	done

	if [ "${machine}" = "cygwin" ] ; then
		apt-cyg install $1
	elif [ "${machine}" = "msys" ] ; then
		pacman -S mingw-w64-x86_64-$1
	elif [ "${machine}" = "linux" ] ; then
		if ! sudo apt-get install $1; then
			# try updating the apt repo
			sudo apt update
			if ! sudo apt-get install $1; then
				echo "Error! Cannot install the package $1. Please install it manually using your package manager!" >&2
				exit 1;
			fi
		fi
	fi
}

echo "Checking the Python version..."
# check python version - should be 3.x ONLY
python_bin="python3"
while true; do
	python_ver=$($python_bin -V 2>&1 | grep -Po '(?<=Python )(.+)')
	if [[ -z "$python_ver" ]] || [[ ! $python_ver =~ ^3\.[56789].* ]] ; then
		echo "Error! Python 3.5 or later is required. It should be installed and added to the PATH!"
		install_package python2
		if [ "${machine}" = "linux" ] ; then
			install_package python2-dev
		fi
	else
		break
	fi
done

# $1 = name, $2 = library name, $3 = package name
function check_library {
	echo "* Checking $1..."
	while true; do
	  if ! command -v pkg-config >/dev/null 2>&1 ; then
		echo "* Missing pkg-config"
		echo "Do you want to download and install it now? (Press 1 or 2)"
		select yn in "Yes" "No"; do
			case $yn in
	   			Yes ) install_package pkg-config; break;;
				No ) exit 1;
			esac
		done
	  fi

		lib=$(pkg-config --libs $2 2>&1 | grep -Po '(\-l'$1')')
		if [[ -z "$lib" ]] ; then
			echo "Error! Library $1 NOT FOUND!"
		else
			echo "* Library $1 FOUND!"
			return
		fi
		install_package $3
	done
}

function install_pip3 {
	pip3installer="https://bootstrap.pypa.io/pip/3.6/get-pip.py"
	dst="/tmp/get-pip.py"
   	download_url $pip3installer $dst
   	$python_bin $dst
   	rm $dst
}

function pip3_install_module {
	# check if pip3 works
	pip_bin="$python_bin -m pip"
	while true; do
		pip3v=$($pip_bin --version 2>&1 | grep -Po '(pip [0-9]+\.[0-9]+.*)')
		if [[ -z "$pip3v" ]] ; then
			echo "* Missing pip3"
			if [ "${machine}" = "linux" ] ; then
				echo "Do you want to download and install it now? (Press 1 or 2)"
				select yn in "Yes" "No"; do
					case $yn in
			   			Yes ) install_pip3; break;;
						No ) exit 1;
					esac
				done
		   	else
		   		install_package pip3
		   	fi
		else
			break
		fi
	done

	# check if gnu compiler works (needed by some modules)
	gcc_bin="gcc"
	while true; do
		gccv=$($gcc_bin -v 2>&1 | grep -Po '(version\s+[0-9]+\.[0-9]+.*)')
		if [[ -z "$gccv" ]] ; then
			echo "* Missing gcc compiler"
  			install_package gcc
		else
			break
		fi
	done

	echo "* Installing python module $1 using $pip3v and gcc $gccv..."
	$pip_bin install $pymodule
}

echo "* Python $python_ver detected!"

echo "Checking git..."
git_bin="git"
git_ver=0
while true; do
	git_ver=$($git_bin version 2>&1 | grep -Po '(version [0-9]+\.[0-9]+.*)')
	if [[ -z "$git_ver" ]] ; then
		echo "Error! Git not found! We need it to update submodules."
		install_package git
	else
		break
	fi
done
echo "* Git $git_ver detected!"

echo "Updating git submodules for scripts..."
#git submodule update --init -- bin/gerbmerge bin/python-combine-pdfs bin/InteractiveHtmlBom bin/pcb-tools

echo "Checking the Python modules..."
declare -A modules
modules[simpleparse]=simpleparse
modules[moderngl]=ModernGL
modules[PIL]=Pillow
modules[pyrr]=Pyrr
modules[numpy]=NumPy
modules[vrml.vrml97]=PyVRML97
modules[contextlib2]=contextlib2
modules[PyPDF2]=PyPDF2
modules[gerber]=gerber
modules[configparser]=configparser
modules[gzip]=gzip
modules[cairocffi]=cairocffi

# check modules
for module in "${!modules[@]}"; do
	pymodule=${modules[$module]}
	while true; do
		$python_bin -c "import sys, pkgutil; sys.path.append('./bin/pcb-tools'); sys.exit(0 if (pkgutil.find_loader('$module')) else 1)"
		if [ $? -eq 0 ]; then
			echo "* Checking Python module '$pymodule': OK"
			break
		else
			echo "* Checking Python module '$pymodule': ERROR!"
			echo "  Python module '$pymodule' is required and NOT found!"
			
			# some modules have dependencies
			if [ "$pymodule" = "cairocffi" ]; then
				if [ "${machine}" = "linux" ] ; then
					devname="dev"
				else
					devname="devel"
				fi
				check_library ffi libffi libffi-${devname}
				check_library cairo cairo libcairo-${devname}
			fi

			if [ ]; then
				echo "Please use 'pip3 install $pymodule' to install it manually!"
				exit 1;
			else
				echo "Do you want to download and install it now? (Press 1 or 2)"
				select yn in "Yes" "No"; do
					case $yn in
						Yes ) pip3_install_module $pymodule; break;;
						No ) exit 1;
					esac
				done
			fi
		fi
	done
done

echo "All checks done!"

exit 0
