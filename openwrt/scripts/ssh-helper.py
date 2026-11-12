import pexpect, sys

def run(cmds, host="192.168.2.1", password="asdf", timeout=300, marker="###END###"):
    c = pexpect.spawn(f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@{host}",
                      timeout=timeout, encoding="utf-8", codec_errors="replace")
    c.expect("assword", timeout=60)
    c.sendline(password)
    c.expect(r"root@[^#]*#", timeout=60)
    out = []
    for cmd in cmds:
        # the marker is assembled at runtime so the echoed command line
        # does not contain the literal marker text
        c.sendline(f"{cmd} ; printf '%s%s\\n' '###EN' 'D###'")
        c.expect(marker, timeout=timeout)
        body = c.before
        # drop the echoed command line
        lines = body.replace("\r\n", "\n").split("\n")
        if lines and cmd.strip()[:20] in lines[0]:
            lines = lines[1:]
        out.append("\n".join(l for l in lines if l.strip() != marker))
    c.close()
    return "\n".join(out)

if __name__ == "__main__":
    cmds = sys.argv[1:]
    print(run(cmds))
