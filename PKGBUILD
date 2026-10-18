# Maintainer: ArchClean Contributors
pkgname=archclean
pkgver=0.1.0
pkgrel=1
pkgdesc="A modern system cleaner for Arch Linux"
arch=('any')
url="https://github.com/example/archclean"
license=('MIT')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita')
makedepends=('python-setuptools')
source=("$pkgname-$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
    cd "$pkgname-$pkgver"
    python setup.py build
}

package() {
    cd "$pkgname-$pkgver"
    python setup.py install --root="$pkgdir" --optimize=1
    install -Dm644 data/archclean.desktop "$pkgdir/usr/share/applications/archclean.desktop"
}
