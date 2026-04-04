#include "linux012.h"

static inline int syscall3(int number, int arg1, int arg2, int arg3)
{
    int result;

    __asm__ volatile ("int $0x80" : "=a" (result) : "0" (number), "b" (arg1), "c" (arg2), "d" (arg3));
    return result;
}

int open(const char *path, int flags, int mode)
{
    return syscall3(5, (int) path, flags, mode);
}

int close(int fd)
{
    return syscall3(6, fd, 0, 0);
}

int read(int fd, void *buffer, unsigned int count)
{
    return syscall3(3, fd, (int) buffer, (int) count);
}

int write(int fd, const void *buffer, unsigned int count)
{
    return syscall3(4, fd, (int) buffer, (int) count);
}

int fork(void)
{
    return syscall3(2, 0, 0, 0);
}

int execve(const char *path, char **argv, char **envp)
{
    return syscall3(11, (int) path, (int) argv, (int) envp);
}

int waitpid(int pid, int *status, int options)
{
    return syscall3(7, pid, (int) status, options);
}

int chdir(const char *path)
{
    return syscall3(12, (int) path, 0, 0);
}

void _exit(int status)
{
    syscall3(1, status, 0, 0);
    for (;;) {
    }
}

unsigned int strlen(const char *text)
{
    unsigned int size = 0;

    while (text[size]) {
        size++;
    }
    return size;
}

int strcmp(const char *left, const char *right)
{
    while (*left && *left == *right) {
        left++;
        right++;
    }
    return (unsigned char) *left - (unsigned char) *right;
}

int strncmp(const char *left, const char *right, unsigned int count)
{
    while (count && *left && *left == *right) {
        left++;
        right++;
        count--;
    }
    if (!count) {
        return 0;
    }
    return (unsigned char) *left - (unsigned char) *right;
}

char *strcpy(char *dest, const char *src)
{
    char *out = dest;

    while ((*dest++ = *src++)) {
    }
    return out;
}

void write_str(int fd, const char *text)
{
    write(fd, text, strlen(text));
}

int read_line(int fd, char *buffer, unsigned int capacity)
{
    unsigned int used = 0;
    char ch = 0;

    while (used + 1 < capacity) {
        int rc = read(fd, &ch, 1);

        if (rc <= 0) {
            break;
        }
        if (ch == '\r') {
            continue;
        }
        if (ch == '\n') {
            break;
        }
        buffer[used++] = ch;
    }
    buffer[used] = '\0';
    return (int) used;
}
