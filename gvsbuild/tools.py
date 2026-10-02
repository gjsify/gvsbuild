#  Copyright (C) 2016 The Gvsbuild Authors
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Default tools used to build the various projects."""

import os
import subprocess

from .utils.base_expanders import extract_exec
from .utils.base_project import Project
from .utils.base_tool import Tool, tool_add
from .utils.utils import is_arm64


def _rustup_arch() -> str:
    """rustup-init host arch, as used in the win.rustup.rs download path."""
    return "aarch64" if is_arm64(Project.opts.platform) else "x86_64"


def _rust_toolchain_arch() -> str:
    """Rust target triple arch, aarch64 is the arm64 one."""
    if Project.opts.x86:
        return "i686"
    return "aarch64" if is_arm64(Project.opts.platform) else "x86_64"


@tool_add
class ToolCargo(Tool):
    def __init__(self):
        Tool.__init__(
            self,
            "cargo",
            version="1.98.1",
            repository="https://github.com/rust-lang/rust",
            archive_url=f"https://win.rustup.rs/{_rustup_arch()}",
            archive_filename="rustup-init.exe",
            exe_name="cargo.exe",
        )

    def load_defaults(self):
        Tool.load_defaults(self)
        self.tool_path = os.path.join(self.build_dir, "bin")
        self.full_exe = os.path.join(self.tool_path, "cargo.exe")

        self.add_extra_env("RUSTUP_HOME", self.build_dir)
        self.add_extra_env("CARGO_HOME", self.build_dir)

    def unpack(self):
        env = os.environ.copy()
        env["RUSTUP_HOME"] = self.build_dir
        env["CARGO_HOME"] = self.build_dir

        toolchain = f"{self.version}-{_rust_toolchain_arch()}-pc-windows-msvc"
        subprocess.run(
            [
                self.archive_file,
                "--no-modify-path",
                "--default-toolchain",
                toolchain,
                "-y",
            ],
            check=True,
            env=env,
        )

        self.mark_deps = True


@tool_add
class ToolCmake(Tool):
    def __init__(self):
        if is_arm64(Project.opts.platform):
            host_part = "arm64"
            host_hash = (
                "7b410ddd00e24c7250eec7452da2348a4a70437aa87e9cda0a20d6a85662fcff"
            )
        else:
            host_part = "x86_64"
            host_hash = (
                "4d52ebab7193a698651639ed80d8d04fd903358843572cf44c7fd234cb7c26ab"
            )
        dir_part = "cmake-{version}-windows-" + host_part
        Tool.__init__(
            self,
            "cmake",
            version="4.4.3",
            repository="https://gitlab.kitware.com/cmake/cmake",
            archive_url="https://github.com/Kitware/CMake/releases/download/v{version}/"
            + dir_part
            + ".zip",
            hash=host_hash,
            dir_part=dir_part,
        )

    def load_defaults(self):
        Tool.load_defaults(self)
        self.tool_path = os.path.join(self.build_dir, "bin")
        self.full_exe = os.path.join(self.tool_path, "cmake.exe")

    def unpack(self):
        self.mark_deps = extract_exec(
            self.archive_file,
            self.opts.tools_root_dir,
            dir_part=self.dir_part,
            check_file=self.full_exe,
            check_mark=True,
        )


@tool_add
class ToolMeson(Tool):
    def __init__(self):
        Tool.__init__(
            self,
            "meson",
            version="1.11.2",
            repository="https://github.com/mesonbuild/meson",
            archive_url="https://github.com/mesonbuild/meson/archive/refs/tags/{version}.tar.gz",
            archive_filename="meson-{version}.tar.gz",
            hash="09cc2faedc61262fc62abf57aa6c47c57a8c0730b950609a0711bbaf587bd133",
            dir_part="meson-{version}",
            exe_name="meson.py",
        )

    def unpack(self):
        self.mark_deps = extract_exec(
            self.archive_file,
            self.builder.opts.tools_root_dir,
            dir_part=self.dir_part,
            check_file=self.full_exe,
            check_mark=True,
            strip_one=True,
        )


@tool_add
class ToolMsys2(Tool):
    def __init__(self):
        Tool.__init__(self, "msys2")
        self.internal = True

    def load_defaults(self):
        Tool.load_defaults(self)
        self.tool_path = os.path.join(self.opts.msys_dir, "usr", "bin")

    def unpack(self):
        self.tool_mark()

    def get_path(self):
        # We always put msys at the end of path
        return None, self.tool_path


@tool_add
class ToolNasm(Tool):
    """The nasm assembler, x86 only.

    There is no arm64 build and we do not need one: nasm is used to assemble
    x86 SIMD code, so the arm64 projects must not depend on it. The tool is
    still available (and runs under the Windows on ARM emulation) for the
    projects that need it, so it is not dropped from the tools group.
    """

    def __init__(self):
        Tool.__init__(
            self,
            "nasm",
            version="3.02",
            repository="https://github.com/netwide-assembler/nasm",
            archive_url="https://www.nasm.us/pub/nasm/releasebuilds/{version}/win64/nasm-{version}-win64.zip",
            hash="161d0bfaff53c2f9e9f3e69fd0672323ebabafd1268976a5cec11be92a19aee7",
            dir_part="nasm-{version}",
            exe_name="nasm.exe",
        )

    def unpack(self):
        # We directly download the exe file, so we copy it on the tool directory
        self.mark_deps = extract_exec(
            self.archive_file,
            self.builder.opts.tools_root_dir,
            dir_part=self.dir_part,
            check_file=self.full_exe,
            force_dest=self.full_exe,
            check_mark=True,
        )


@tool_add
class ToolNinja(Tool):
    def __init__(self):
        if is_arm64(Project.opts.platform):
            # Upstream names the arm64 asset 'ninja-winarm64.zip' and does not
            # prefix the version, so the local file name must stay unique or
            # the two platforms would share one file in the download dir. The
            # tool dir is per platform for the same reason: the x64 ninja is
            # not re-downloaded for the arm64 build.
            win_part = "winarm64"
            win_hash = (
                "e52f0bdef9dfb1003229dbd6508a508c4073fd017247002adc66e5e806cb0391"
            )
            dir_part = "ninja-winarm64-{version}"
        else:
            win_part = "win"
            win_hash = (
                "07fc8261b42b20e71d1720b39068c2e14ffcee6396b76fb7a795fb460b78dc65"
            )
            dir_part = "ninja-{version}"
        Tool.__init__(
            self,
            "ninja",
            version="1.13.2",
            repository="https://github.com/ninja-build/ninja",
            archive_url="https://github.com/ninja-build/ninja/releases/download/v{version}/ninja-"
            + win_part
            + ".zip",
            archive_filename="ninja-" + win_part + "-{version}.zip",
            hash=win_hash,
            dir_part=dir_part,
            exe_name="ninja.exe",
        )

    def unpack(self):
        self.mark_deps = extract_exec(
            self.archive_file, self.build_dir, check_file=self.full_exe, check_mark=True
        )


@tool_add
class ToolPerl(Tool):
    """Strawberry Perl, x64 only.

    There is no upstream arm64 build, but perl is a build-time script
    interpreter, not a library of the stack, so the x64 build runs fine under
    the Windows on ARM emulation and we keep using it unchanged.
    """

    def __init__(self):
        Tool.__init__(
            self,
            "perl",
            version="5.20.0",
            outdated_skip=True,
            repository="https://github.com/Perl/perl5",
            archive_url="https://github.com/wingtk/gtk-win32/releases/download/Perl-{major}.{minor}/perl-{version}-x64.tar.xz",
            hash="05e01cf30bb47d3938db6169299ed49271f91c1615aeee5649174f48ff418c55",
            dir_part="perl-{version}",
        )

    def load_defaults(self):
        Tool.load_defaults(self)
        # Set the builder object to point to the path to use, when we need to pass directly the executable to *make
        self.base_dir = os.path.join(self.build_dir, "x64")
        # full path, added to the environment when needed
        self.tool_path = os.path.join(self.base_dir, "bin")
        self.full_exe = os.path.join(self.tool_path, "perl.exe")

    def unpack(self):
        self.mark_deps = extract_exec(
            self.archive_file, self.build_dir, check_file=self.full_exe, check_mark=True
        )

    def get_base_dir(self):
        return self.base_dir


@tool_add
class ToolGo(Tool):
    def __init__(self):
        if is_arm64(Project.opts.platform):
            go_part = "arm64"
            go_hash = "13b69b87bb0e83f96bc68560a8cace7f0343b1e03469f1110ea18d17e3234069"
            dir_part = "go-arm64-{version}"
        else:
            go_part = "amd64"
            go_hash = "a3911b5e0e1b1053f25ed0675f4c1c6aad1e2bfcf253df2b9be4caabd2edd95d"
            dir_part = "go-{version}"
        Tool.__init__(
            self,
            "go",
            version="1.27.1",
            repository="https://github.com/golang/go",
            archive_url="https://go.dev/dl/go{version}.windows-" + go_part + ".zip",
            hash=go_hash,
            dir_part=dir_part,
        )

    def load_defaults(self):
        Tool.load_defaults(self)
        self.tool_path = os.path.join(self.build_dir, "bin")
        self.full_exe = os.path.join(self.tool_path, "go.exe")

    def unpack(self):
        # We download directly the exe file, so we copy it to the tool directory
        self.mark_deps = extract_exec(
            self.archive_file,
            self.build_dir,
            check_file=self.full_exe,
            check_mark=True,
            strip_one=True,
        )
