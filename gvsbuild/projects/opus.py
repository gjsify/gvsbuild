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

from gvsbuild.utils.base_builders import Meson
from gvsbuild.utils.base_expanders import Tarball
from gvsbuild.utils.base_project import project_add


@project_add
class Opus(Tarball, Meson):
    def __init__(self):
        Meson.__init__(
            self,
            "opus",
            version="1.6.1",
            repository="https://github.com/xiph/opus",
            archive_url="https://downloads.xiph.org/releases/opus/opus-{version}.tar.gz",
            hash="6ffcb593207be92584df15b32466ed64bbec99109f007c82205f0194572411a1",
            dependencies=[
                "ninja",
                "meson",
                "pkgconf",
            ],
        )
        self.add_param("-Dtests=disabled")
        self.add_param("-Ddocs=disabled")

    def build(self):
        meson_params = []
        if self.builder.arm64:
            # opus' NEON detection only asks whether <arm_neon.h> compiles, so
            # it finds NEON on an MSVC arm64 target and builds
            # dnn/arm/nnet_neon.c -- which then refuses to compile because it
            # requires __ARM_NEON/__ARM_NEON__. Those are GCC and clang
            # spellings MSVC never defines: NEON is part of the arm64 baseline,
            # so MSVC has no reason to advertise it. We build opus without
            # deep-plc, where the intrinsics would matter, so turn them off
            # instead of patching the compiler's predefined macros.
            meson_params.append("-Dintrinsics=disabled")
        Meson.build(self, meson_params=meson_params)
        self.install(r"COPYING share\doc\opus")
