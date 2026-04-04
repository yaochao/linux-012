ENTRY(_start)

SECTIONS
{
    . = 0;
    .text : { *(.text*) *(.rodata*) }
    . = ALIGN(1024);
    __data_start = .;
    .data : { *(.data*) }
    . = ALIGN(4);
    __bss_start = .;
    .bss : { *(.bss*) *(COMMON) }
    __bss_end = .;
}
