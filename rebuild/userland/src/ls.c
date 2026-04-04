#include "linux012.h"

static struct linux012_dirent entries[64];

static int is_dot_entry(const char *name)
{
    if (name[0] != '.') {
        return 0;
    }
    if (!name[1]) {
        return 1;
    }
    return name[1] == '.' && !name[2];
}

static void write_name(const char *name)
{
    char buffer[15];
    int index = 0;

    while (index < 14 && name[index]) {
        buffer[index] = name[index];
        index++;
    }
    buffer[index] = '\0';
    write_str(1, buffer);
}

int main(void)
{
    int fd = open(".", O_RDONLY, 0);
    int size;
    int index;

    if (fd < 0) {
        write_str(2, "ls: cannot open .\n");
        return 1;
    }
    size = read(fd, entries, sizeof(entries));
    close(fd);
    if (size < 0) {
        write_str(2, "ls: cannot read .\n");
        return 1;
    }
    for (index = 0; index < size / (int) sizeof(struct linux012_dirent); ++index) {
        if (!entries[index].inode || !entries[index].name[0] || is_dot_entry(entries[index].name)) {
            continue;
        }
        write_name(entries[index].name);
        write_str(1, "\n");
    }
    return 0;
}
