// The existing Xcode target builds Mellow/ translation units. This single
// integration unit compiles the reviewed portable Xe subsystem into that target.
// Do not also compile Drivers/PortedXe/XePageTable.cpp in the same target.
// Included code retains its upstream MIT notices and provenance.
#include "../Drivers/PortedXe/XePageTable.cpp"
