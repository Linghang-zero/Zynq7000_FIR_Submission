connect
targets -set -filter {name =~ "ARM Cortex-A9 MPCore #0"}
dow D:/fp_perf_build/fir_test.elf
puts "=== RUN (no breakpoints, clean timing) ==="
con
after 5000
puts "=== STATE ==="
puts [state]
stop
after 500
puts "=== DUMP RxBuffer (mixed output, clean run) ==="
set f [open D:/fp_perf_build/mixed_dump_clean.txt w]
set vals [mrd -value 0x001117C0 1000]
foreach v $vals {
    puts $f [format %08x $v]
}
close $f
puts "mixed clean dump written, [llength $vals] words"
puts "=== READ VARIABLES (clean) ==="
puts "test_status      : [mrd 0x00112760 1]"
puts "completed_samples: [mrd 0x00112764 1]"
puts "hw_sine_cycles   : [mrd 0x001146e8 2]"
puts "hw_sine_us       : [mrd 0x001146f8 2]"
puts "hw_mixed_cycles  : [mrd 0x001146f0 2]"
puts "hw_mixed_us      : [mrd 0x00114700 2]"
puts "sw_sine_us       : [mrd 0x001146c8 2]"
puts "sw_mixed_us      : [mrd 0x001146d0 2]"
puts "=== DONE ==="
exit
