#!/usr/bin/expect

set old_password [lindex $argv 0]
set new_password [lindex $argv 1]

if { $old_password == "" || $new_password == "" } {
    puts "no arguments"
    exit 1
}

spawn kpasswd

expect {
    "Password for" { send -- "$old_password\r" }
    default { exit 1 }
}
expect {
    "Enter new password:" { send -- "$new_password\r" }
    default { exit 1 }
}
expect {
    "Enter it again:" { send -- "$new_password\r" }
    default { exit 1 }
}
expect eof
exit 0