#include "linux012.h"

static char line[128];
static char cwd[64] = "/";

static void print_prompt(void)
{
    write_str(1, "[");
    write_str(1, cwd);
    write_str(1, "]# ");
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

int main(int argc, char **argv, char **envp)
{
    int interactive = argc > 0 && argv[0] && argv[0][0] == '-';

    if (chdir("/usr/root") == 0) {
        strcpy(cwd, "/usr/root");
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
        if (strncmp(line, "cd ", 3) == 0) {
            if (chdir(line + 3) == 0) {
                strcpy(cwd, line + 3);
            } else {
                write_str(2, "cd: no such directory\n");
            }
            continue;
        }
        if (strcmp(line, "exit") == 0) {
            return 0;
        }
        write_str(2, "unsupported command\n");
    }
}
