# Hướng dẫn cài đặt Neovim trên Raspberry Pi (pi4-tdbao.local)

Config gốc: https://github.com/ncongduy/my-vim-config.git

> Repo này có 2 phần config (Vim và Neovim). Ở đây ta setup **Neovim**, dùng file `init.vim` có sẵn trong repo (repo đã có sẵn `init.vim` dành riêng cho Neovim, không cần tự viết lại từ `.vimrc`).

## Thông tin máy đích

- Host: `pi4-tdbao.local` (Raspberry Pi 4 Model B)
- Hệ điều hành: Debian GNU/Linux 13 (trixie), kiến trúc **aarch64 (arm64)**

⚠️ **Lưu ý khác biệt so với README gốc của repo:** README gốc hướng dẫn tải Neovim bản dựng sẵn `nvim-linux64.tar.gz` (bản x86_64) từ GitHub Releases. Bản này **không chạy được trên Raspberry Pi (arm64)**. Vì vậy bước cài Neovim bên dưới dùng gói Neovim 0.10.4 từ kho apt chính thức của Debian (đã build sẵn cho arm64) thay vì tải tarball. Các bước còn lại (vim-plug, `init.vim`, plugin...) giữ nguyên như repo gốc.

## Bước 1: Cập nhật gói và cài Neovim + các công cụ hỗ trợ

```bash
sudo apt-get update
sudo apt-get install -y neovim nodejs npm universal-ctags xclip ripgrep
```

Giải thích các gói:
- `neovim` — bản thay thế cho bước tải tarball trong README gốc (tương đương, phù hợp arm64)
- `nodejs`, `npm` — bắt buộc để cài `coc.nvim` (chạy `npm ci`) và `markdown-preview.nvim` (chạy `npm install`)
- `universal-ctags` — cần cho plugin Tagbar (README gốc có ghi chú mục "Fix ctags error")
- `xclip` — copy/paste giữa tmux và clipboard hệ thống
- `ripgrep` — dùng cho `:grep` nhanh trong Neovim (theo hướng dẫn trong `neovim-search-workflow.md` của repo)

Kiểm tra:

```bash
nvim --version   # NVIM v0.10.4
node --version   # v20.19.2
npm --version    # 9.2.0
```

## Bước 2: Cài vim-plug (trình quản lý plugin)

```bash
curl -fLo ~/.local/share/nvim/site/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
```

## Bước 3: Tải config từ repo và đặt vào đúng vị trí

```bash
git clone --depth 1 https://github.com/ncongduy/my-vim-config.git ~/my-vim-config-src

mkdir -p ~/.config/nvim
cp ~/my-vim-config-src/init.vim ~/.config/nvim/init.vim
cp ~/my-vim-config-src/coc-settings.json ~/.config/nvim/coc-settings.json
```

- `init.vim` → cấu hình chính của Neovim (theme, NERDTree, coc.nvim, fzf, tagbar, keymap...)
- `coc-settings.json` → cấu hình riêng cho coc.nvim (format on save cho JS/TS/JSON...)

## Bước 4: Cài toàn bộ plugin khai báo trong `init.vim`

Chạy Neovim ở chế độ headless để cài hết plugin mà không cần mở giao diện:

```bash
nvim --headless "+PlugInstall --sync" +qa
```

Lệnh này sẽ tự động tải và cài các plugin sau (khai báo trong `init.vim`):

| Plugin | Chức năng |
|---|---|
| vim-airline, vim-airline-themes | Thanh trạng thái |
| nerdtree, nerdtree-git-plugin, vim-nerdtree-syntax-highlight | Trình duyệt file bên trái + icon git |
| fzf, fzf.vim | Fuzzy finder tìm file (`Ctrl-P`) |
| auto-pairs | Tự đóng ngoặc |
| coc.nvim | Autocomplete / LSP (chạy `npm ci` khi cài) |
| vim-visual-multi | Multiple cursors |
| vim-css-color | Preview màu CSS |
| vim-commentary | Comment nhanh (`gcc`, `gc`) |
| vim-fugitive | Tích hợp Git |
| tagbar | Xem outline hàm/class (`F8`) |
| awesome-vim-colorschemes | Bộ theme màu |
| markdown-preview.nvim | Xem trước Markdown (chạy `npm install` khi cài) |

Kiểm tra plugin đã cài đủ:

```bash
ls ~/.local/share/nvim/plugged/
```

## Bước 5: Kiểm tra Neovim chạy sạch (không lỗi khi khởi động)

```bash
nvim --headless -c "sleep 300m" -c "qa"
```

Nếu không có output/lỗi in ra là config đã load thành công.

## (Tùy chọn) Cài thêm ngôn ngữ hỗ trợ cho coc.nvim

Mở `nvim` bình thường rồi chạy các lệnh sau (bên trong Neovim) tùy nhu cầu ngôn ngữ đang dùng:

```vim
:CocInstall coc-tsserver     " TypeScript / JavaScript / TSX / JSX
:CocInstall coc-html         " HTML
:CocInstall coc-css          " CSS
:CocInstall coc-json         " JSON
:CocInstall coc-java         " Java
:CocInstall coc-pyright      " Python
:CocInstall coc-yaml         " YAML
:CocInstall coc-docker       " Dockerfile
:CocInstall coc-flutter      " Flutter
```

Xem danh sách extension đã cài: `:CocList extensions`
Gỡ extension: `:CocUninstall <tên>`

## Một số phím tắt chính (đã cấu hình sẵn trong `init.vim`)

| Phím | Chức năng |
|---|---|
| `<leader>n` | Focus vào NERDTree |
| `Ctrl-t` | Bật/tắt NERDTree |
| `Ctrl-p` | Fuzzy search file (fzf) |
| `F8` | Bật/tắt Tagbar |
| `gd` | Coc: Go to definition |
| `gy` | Coc: Go to type definition |
| `gi` | Coc: Go to implementation |
| `gr` | Coc: Go to references |
| `K` | Xem tài liệu (hover) |
| `<leader>rn` | Coc: Rename symbol |
| `<leader>f` | Coc: Format đoạn code đã chọn |

## Kết quả sau khi cài

- Neovim: `0.10.4` (từ apt, arm64)
- Vị trí config: `~/.config/nvim/init.vim`, `~/.config/nvim/coc-settings.json`
- Plugin manager: vim-plug tại `~/.local/share/nvim/site/autoload/plug.vim`
- Toàn bộ plugin nằm tại `~/.local/share/nvim/plugged/`
