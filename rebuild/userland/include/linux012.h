#ifndef REBUILD_USERLAND_LINUX012_H
#define REBUILD_USERLAND_LINUX012_H

#define NULL ((void *)0)
#define O_RDONLY 0
#define O_WRONLY 1
#define O_RDWR 2

struct linux012_dirent {
    unsigned short inode;
    char name[14];
};

int open(const char *path, int flags, int mode);
int close(int fd);
int read(int fd, void *buffer, unsigned int count);
int write(int fd, const void *buffer, unsigned int count);
int fork(void);
int execve(const char *path, char **argv, char **envp);
int waitpid(int pid, int *status, int options);
int chdir(const char *path);
void _exit(int status);

unsigned int strlen(const char *text);
int strcmp(const char *left, const char *right);
int strncmp(const char *left, const char *right, unsigned int count);
char *strcpy(char *dest, const char *src);
void write_str(int fd, const char *text);
int read_line(int fd, char *buffer, unsigned int capacity);

#endif
