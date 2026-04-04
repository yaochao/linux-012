    .globl _start
_start:
    popl %eax
    popl %ebx
    popl %ecx
    pushl %ecx
    pushl %ebx
    pushl %eax
    call main
    movl %eax, %ebx
    movl $1, %eax
    int $0x80
