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

import os

from gvsbuild.utils.base_expanders import Tarball
from gvsbuild.utils.base_project import Project, project_add
from gvsbuild.utils.utils import file_replace


@project_add
class Zlib(Tarball, Project):
    def __init__(self):
        Project.__init__(
            self,
            "zlib",
            version="1.3.2",
            repository="https://github.com/madler/zlib",
            archive_url="https://github.com/madler/zlib/releases/download/v{version}/zlib-{version}.tar.xz",
            hash="d7a0654783a4da529d1bb793b7ad9c3318020af77667bcae35f95d0e42a792f3",
            patches=[],
        )

    def build(self):
        if self.builder.arm64:
            # The makefile pins the DLL to a fixed base below 4 GB, which the
            # ARM64 linker rejects (LNK1355).
            file_replace(
                os.path.join(self.build_dir, "win32", "Makefile.msc"),
                [(r" -base:0x[0-9A-Fa-f]+", "")],
            )
        cmd = [
            "nmake",
            "/nologo",
            r"/f",
            r"win32\Makefile.msc",
            "STATICLIB=zlib-static.lib",
            "IMPLIB=zlib1.lib",
        ]
        if self.builder.opts.configuration == "debug":
            cmd.append(r'CFLAGS=-nologo -MDd -W3 -Od -Zi -Fd"zlib"')
        self.exec_vs(cmd)

        self.install(r".\zlib.h .\zconf.h include")
        self.install(r".\zlib1.dll .\zlib1.pdb bin")
        self.install(r".\zlib1.lib lib")

        self.install_pc_files()
        self.install(r".\README share\doc\zlib")
