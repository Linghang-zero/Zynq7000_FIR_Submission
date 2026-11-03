setws D:/fp_perf_build/ws
importprojects D:/fp_perf_build/fir_test_perf_bsp
importprojects D:/fp_perf_build/fir_test_perf
puts "=== PROJECTS ==="
projects
puts "=== BUILD ==="
projects -build -name fir_test -type app
puts "=== BUILD DONE ==="
exit
