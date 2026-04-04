#include "linux012.h"

#define LINE_CAPACITY 128
#define CWD_CAPACITY 64
#define SEGMENT_CAPACITY 32
#define CAT_BUFFER_CAPACITY 128
#define SHELL_HOME "/usr/root"

static char line[LINE_CAPACITY];
static char cwd[CWD_CAPACITY] = "/";

static void print_prompt(void)
{
    write_str(1, "[");
    write_str(1, cwd);
    write_str(1, "]# ");
}

static void write_line(int fd, const char *text)
{
    write_str(fd, text);
    write_str(fd, "\n");
}

static int run_ls(char **envp)
{
    int status = 0;
    char *argv[] = { "/bin/ls", NULL };
    int pid = fork();

    if (pid == 0) {
        execve("/bin/ls", argv, envp);
        _exit(127);
    }
    if (pid < 0) {
        write_str(2, "cannot fork\n");
        return 1;
    }
    waitpid(pid, &status, 0);
    return status;
}

static void trim_last_segment(char *path)
{
    int length = (int) strlen(path);

    while (length > 1 && path[length - 1] == '/') {
        path[--length] = '\0';
    }
    while (length > 1 && path[length - 1] != '/') {
        length--;
    }
    if (length <= 1) {
        path[0] = '/';
        path[1] = '\0';
        return;
    }
    path[length - 1] = '\0';
}

static void append_path_segment(char *path, const char *segment)
{
    int length = (int) strlen(path);
    int used = 0;

    if (!(path[0] == '/' && !path[1])) {
        path[length++] = '/';
    }
    while (segment[used] && length + 1 < CWD_CAPACITY) {
        path[length++] = segment[used++];
    }
    path[length] = '\0';
}

static void normalize_path(char *path, const char *target)
{
    char next[CWD_CAPACITY];
    char segment[SEGMENT_CAPACITY];
    const char *cursor = target;
    int used;

    if (target[0] == '/') {
        next[0] = '/';
        next[1] = '\0';
    } else {
        strcpy(next, path);
    }

    while (*cursor) {
        while (*cursor == '/') {
            cursor++;
        }
        if (!*cursor) {
            break;
        }
        used = 0;
        while (*cursor && *cursor != '/') {
            if (used + 1 < SEGMENT_CAPACITY) {
                segment[used++] = *cursor;
            }
            cursor++;
        }
        segment[used] = '\0';
        if (strcmp(segment, ".") == 0) {
            continue;
        }
        if (strcmp(segment, "..") == 0) {
            trim_last_segment(next);
            continue;
        }
        append_path_segment(next, segment);
    }

    strcpy(path, next);
}

static int change_directory(const char *target)
{
    if (chdir(target) != 0) {
        write_str(2, "cd: no such directory\n");
        return 1;
    }
    normalize_path(cwd, target);
    return 0;
}

static void run_pwd(void)
{
    write_line(1, cwd);
}

static void run_echo(const char *text)
{
    write_line(1, text);
}

static int run_cat(const char *path)
{
    char buffer[CAT_BUFFER_CAPACITY];
    int fd = open(path, O_RDONLY, 0);

    if (fd < 0) {
        write_str(2, "cat: cannot open ");
        write_line(2, path);
        return 1;
    }
    while (1) {
        int size = read(fd, buffer, sizeof(buffer));

        if (size < 0) {
            close(fd);
            write_str(2, "cat: cannot read ");
            write_line(2, path);
            return 1;
        }
        if (size == 0) {
            break;
        }
        write(1, buffer, (unsigned int) size);
    }
    close(fd);
    return 0;
}

static void run_uname(const char *args)
{
    if (!args[0] || strcmp(args, "-a") == 0) {
        write_str(1, "Linux 0.12\n");
        return;
    }
    write_str(2, "uname: unsupported option\n");
}

int main(int argc, char **argv, char **envp)
{
    int interactive = argc > 0 && argv[0] && argv[0][0] == '-';

    if (chdir(SHELL_HOME) == 0) {
        strcpy(cwd, SHELL_HOME);
    }

    while (1) {
        if (interactive) {
            print_prompt();
        }
        if (read_line(0, line, sizeof(line)) <= 0) {
            return 0;
        }
        if (!line[0] || line[0] == '#') {
            continue;
        }
        if (strcmp(line, "ls") == 0) {
            run_ls(envp);
            continue;
        }
        if (strcmp(line, "pwd") == 0) {
            run_pwd();
            continue;
        }
        if (strcmp(line, "echo") == 0) {
            run_echo("");
            continue;
        }
        if (strncmp(line, "echo ", 5) == 0) {
            run_echo(line + 5);
            continue;
        }
        if (strncmp(line, "cat ", 4) == 0) {
            run_cat(line + 4);
            continue;
        }
        if (strcmp(line, "uname") == 0) {
            run_uname("");
            continue;
        }
        if (strcmp(line, "uname -a") == 0) {
            run_uname("-a");
            continue;
        }
        if (strcmp(line, "cd") == 0) {
            change_directory(SHELL_HOME);
            continue;
        }
        if (strncmp(line, "cd ", 3) == 0) {
            change_directory(line + 3);
            continue;
        }
        if (strcmp(line, "exit") == 0) {
            return 0;
        }
        write_str(2, "unsupported command\n");
    }
}
