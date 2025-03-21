; Простой загрузчик, который печатает сообщение и застревает в цикле.

section .text
    ; BIOS загружает код в память по адресу 0x7c00.
    org 0x7c00

start:
    ; Установка режима BIOS для вывода текста.
    mov ah, 0x0e

    ; Печать сообщения.
    mov al, 'H'
    int 0x10
    mov al, 'e'
    int 0x10
    mov al, 'l'
    int 0x10
    mov al, 'l'
    int 0x10
    mov al, 'o'
    int 0x10
    mov al, ','
    int 0x10
    mov al, ' '
    int 0x10
    mov al, 'W'
    int 0x10
    mov al, 'o'
    int 0x10
    mov al, 'r'
    int 0x10
    mov al, 'l'
    int 0x10
    mov al, 'd'
    int 0x10
    mov al, '!'
    int 0x10

    ; Переход на новую строку.
    mov al, 0x0A
    int 0x10
    mov al, 0x0D
    int 0x10

    ; Бесконечный цикл.
loop_forever:
    jmp loop_forever

; Заполнение остальной части сектора нулями.
times 510-($-$$) db 0

; BIOS магическое число.
dw 0xaa55
