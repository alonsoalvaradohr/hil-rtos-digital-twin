# Auto-start labwc on tty1
if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi

if [ -z "$WAYLAND_DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec labwc
fi