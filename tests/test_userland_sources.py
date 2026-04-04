import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class UserlandSourceTest(unittest.TestCase):
    def test_crt0_reads_linux012_stack_as_argc_argv_envp_triplet(self) -> None:
        text = (ROOT / "rebuild" / "userland" / "src" / "crt0.S").read_text(encoding="utf-8")

        self.assertIn("popl %eax", text)
        self.assertIn("popl %ebx", text)
        self.assertIn("popl %ecx", text)
        self.assertNotIn("movl %esp, %ebx", text)

    def test_linux012_header_declares_14_char_directory_entries(self) -> None:
        text = (ROOT / "rebuild" / "userland" / "include" / "linux012.h").read_text(encoding="utf-8")

        self.assertIn("struct linux012_dirent", text)
        self.assertIn("char name[14];", text)
        self.assertIn("int execve", text)

    def test_shell_source_execs_bin_ls_and_uses_usr_root_prompt(self) -> None:
        text = (ROOT / "rebuild" / "userland" / "src" / "sh.c").read_text(encoding="utf-8")

        self.assertIn('"/bin/ls"', text)
        self.assertIn('"/usr/root"', text)
        self.assertIn('"]# "', text)

    def test_shell_source_provides_pwd_echo_cat_and_uname_builtins(self) -> None:
        text = (ROOT / "rebuild" / "userland" / "src" / "sh.c").read_text(encoding="utf-8")

        self.assertIn('strcmp(line, "pwd")', text)
        self.assertIn('strcmp(line, "echo")', text)
        self.assertIn('strncmp(line, "echo ", 5)', text)
        self.assertIn('strncmp(line, "cat ", 4)', text)
        self.assertIn('strcmp(line, "uname")', text)
        self.assertIn('strcmp(line, "uname -a")', text)
        self.assertIn("open(path, O_RDONLY, 0)", text)
        self.assertIn("write_str(1, cwd)", text)

    def test_shell_source_normalizes_cwd_when_cd_succeeds(self) -> None:
        text = (ROOT / "rebuild" / "userland" / "src" / "sh.c").read_text(encoding="utf-8")

        self.assertIn("normalize_path", text)
        self.assertIn("trim_last_segment", text)
        self.assertIn("append_path_segment", text)

    def test_ls_source_reads_linux012_directory_entries(self) -> None:
        text = (ROOT / "rebuild" / "userland" / "src" / "ls.c").read_text(encoding="utf-8")

        self.assertIn("struct linux012_dirent", text)
        self.assertIn("O_RDONLY", text)
        self.assertIn("write_str", text)


if __name__ == "__main__":
    unittest.main()
