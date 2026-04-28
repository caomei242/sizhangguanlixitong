#include <fcntl.h>
#include <stdarg.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

static const char *REPO_DIR = "/Users/gd/Desktop/副业--草莓私帐管理系统";
static const char *SRC_DIR = "/Users/gd/Desktop/副业--草莓私帐管理系统/src";
static const char *PYTHON_BIN = "/Applications/Xcode.app/Contents/Developer/usr/bin/python3";
static const char *LOG_PATH = "/tmp/private-ledger-launcher.log";
static const char *APP_BUNDLE = "/Users/gd/Desktop/草莓私帐管理系统.app";

static void write_log(const char *fmt, ...) {
    FILE *fp = fopen(LOG_PATH, "a");
    if (!fp) {
        return;
    }
    va_list args;
    va_start(args, fmt);
    vfprintf(fp, fmt, args);
    va_end(args);
    fputc('\n', fp);
    fclose(fp);
}

static pid_t find_running_pid(void) {
    FILE *pipe = popen("pgrep -fo '[p]rivate_ledger\\.app' | head -n 1", "r");
    if (!pipe) {
        write_log("find_running_pid popen failed");
        return -1;
    }

    char buffer[64];
    if (!fgets(buffer, sizeof(buffer), pipe)) {
        pclose(pipe);
        return -1;
    }
    pclose(pipe);
    return (pid_t)strtol(buffer, NULL, 10);
}

static int activate_existing_app(pid_t running_pid) {
    pid_t child = fork();
    if (child < 0) {
        write_log("activate fork failed");
        return -1;
    }
    if (child == 0) {
        char script[192];
        snprintf(
            script,
            sizeof(script),
            "tell application \"Python\" to activate"
        );
        execl(
            "/usr/bin/osascript",
            "osascript",
            "-e",
            script,
            (char *)NULL
        );
        _exit(127);
    }
    write_log("activate requested via osascript for pid=%d", (int)running_pid);
    return 0;
}

static void exec_python_app(void) {
    if (chdir(REPO_DIR) != 0) {
        write_log("exec chdir failed");
        _exit(120);
    }

    setenv("PYTHONPATH", SRC_DIR, 1);
    setenv("QT_QPA_PLATFORM", "cocoa", 1);
    write_log("exec env set PYTHONPATH=%s", SRC_DIR);

    int log_fd = open(LOG_PATH, O_WRONLY | O_CREAT | O_APPEND, 0644);
    if (log_fd >= 0) {
        dup2(log_fd, STDOUT_FILENO);
        dup2(log_fd, STDERR_FILENO);
        close(log_fd);
    }

    int null_fd = open("/dev/null", O_RDONLY);
    if (null_fd >= 0) {
        dup2(null_fd, STDIN_FILENO);
        close(null_fd);
    }

    write_log("exec python=%s", PYTHON_BIN);
    execl(
        PYTHON_BIN,
        "python3",
        "-m",
        "private_ledger.app",
        (char *)NULL
    );
    write_log("exec failed");
    _exit(127);
}

int main(void) {
    pid_t running_pid = find_running_pid();
    write_log("main running_pid=%d", (int)running_pid);
    if (running_pid > 0) {
        write_log("main existing app detected; requesting activation");
        activate_existing_app(running_pid);
        return 0;
    }

    write_log("main launch requested via exec; no detached child");
    exec_python_app();
    return 127;
}
