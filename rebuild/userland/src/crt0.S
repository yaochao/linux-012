    .globl _start
_start:
    popl %eax
    movl %esp, %ebx
    leal 4(%esp,%eax,4), %ecx
    pushl %ecx
    pushl %ebx
    pushl %eax
    call main
    movl %eax, %ebx
    movl $1, %eax
    int $0x80
