foreach possiblePath {/usr/local/include/rtc/rtc.h /usr/include/rtc/rtc.h} {
    if {[file exists $possiblePath]} {
	set headerPath $possiblePath
    }
}

proc snakeCase val {
    # HelloWorld -> hello_world
    join [lmap word [regexp -all -inline {[A-Z][a-z]*} $val] {string tolower $word}] _
}

proc pythonArgsFromCArgs val {
    # `const char * lol, int kek` -> `lol, kek`
    set pythonArgs [join [lmap pair [split $val ,] {
	string map {* "" " " ""} [lindex $pair end]
    }] ", "]
}

proc pythonizeEnumName name {
    # rtcGatheringState -> GatheringState
    # remove "rtc"
    set name [string range $name 3 end]
    # capitalize class name
    set name [string totitle $name 0 0]
}

proc argsToTclList val {
    # outputs like:
    # {int pc  char* cand  char* mid void* ptr}
    # so you can iterate it with foreach {type argname}
    set val [string map {, "" " *" "* " const ""} $val]
}

# make header digestable for python cffi
set header [string trim [exec sed  -e {1,/\/\/ libdatachannel C API/d} \
			     -e {s/RTC_API //} \
			     -e {s/RTC_C_EXPORT //} \
			     -e {/#if*/d} \
			     -e {/#endif*/d} \
			     -e {/\} \/\/ extern "C"/d} \
			     $headerPath]]

proc pythonMarshalArgsForDef {argList} {
    global enums
    set pythonCbMarshal  {}
    foreach {type arg} $argList {
	
	if {$type in "int char*"} {
	    append pythonCbMarshal "$arg, "
	    continue
	}
	set pythonicType [pythonizeEnumName $type]
	if {$pythonicType in $enums} {
	    append pythonCbMarshal "$pythonicType\($arg\), "
	} else {
	    error "idk what to do: $pythonicType"
	}
    }
    set pythonCbMarshal
}

proc pythonMarshalArgsForCb {argList} {
    global enums
    # puts $argList
    set pythonCbMarshal  {}
    foreach {type arg} $argList {
	if {$type == "int"} {
	    if {$arg in "tr dc"} {
		set class [dict get {tr Track dc DataChannel} $arg]
		append pythonCbMarshal "$class.get_by_id($arg), "
		continue
	    }
	}
	if {$type == "char*"} {
	    # append pythonCbMarshal "ffi.string($arg).decode(), "
	    append pythonCbMarshal "ffi.string($arg), "
	    continue
	}
	if {$type in "int char*"} {
	    append pythonCbMarshal "$arg, "
	    continue
	}
	set pythonicType [pythonizeEnumName $type]
	if {$pythonicType in $enums} {
	    append pythonCbMarshal "$pythonicType\($arg\), "
	} else {
	    error "idk what to do: $pythonicType"
	}
    }
    set pythonCbMarshal
}


proc doCallbackTypes {header} {
    global cbArgs
    # walk over callback types and store what args they need
    foreach {- cbName args} [regexp -inline -all {typedef void\(\*([^\)]*)\)\((int [^\)]*)} $header] {
	# remove newlines
	set args [string map {\n " "} $args]
	# zap whitespace
	set args [regsub -all {\s+} $args { }]
	set pythonArgs [join [
			      lmap pair [split $args ,] {
				  string map {* "" " " ""} [lindex $pair end]
			      }
			     ] \
			    ", "]
	set cbArgs($cbName) $args
    }
}


proc doEnums {header} {
    # returns string with python enum declarations
    # adds pythonized names to ::enums
    foreach {- e name} [regexp -inline -all {enum \{([^\}]*)\s+\}([^;]*)} $header] {
	# remove comments
	set e [regsub -all -line {//.*} $e { }] 
	# remove commas and equals signs
	set e [string map {, "" = ""} $e]
	# zap whitespace
	set e [regsub -all {\s+} $e { }]
	# trim
	set e [string trim $e]
	set name [string trim $name]
	set name [pythonizeEnumName $name]
	lappend ::enums $name
	append res "class $name\(Enum\):\n"
	foreach {k v} $e {
	    #remove "RTC"
	    set k [string range $k 4 end]
	    append res "    $k=$v\n"
	}
	append res \n
    }
    set res
}

proc generateCallbacks {header} {
    global initializeToNone
    global res  ;# our result
    global enums ;# from doEnums
    global cbArgs ;# from doCallbackTypes
    foreach {- setter which cbType} [regexp -inline -line -all {int (rtcSet.*Callback)\(int (..), (\S+)} $header] {
	set assocDict [dict get {pc PeerConnection.assoc id CommonChannel.assoc} $which]

	if {![info exists cbArgs($cbType)]} {
	    # this is specifically for rtcInterceptorCallbackFunc so far - no need + no time on my side
	    puts "Skipping $cbType"
	    continue
	}
	
	set pythonCallbackName [snakeCase [string range $setter 6 end]]
	# cdef
	append res(cbs) "extern \"Python\" void wrapper_$pythonCallbackName\($cbArgs($cbType)\);\n"

	append res(cbs_defs) "@ffi.def_extern()\n"
	append res(cbs_defs) "def wrapper_$pythonCallbackName\([pythonArgsFromCArgs $cbArgs($cbType)]\):\n"
	append res(cbs_defs) "    cb = $assocDict\[$which\].$pythonCallbackName\n"
	
	# convert to Tcl list
	# discard void *
	set argList [argsToTclList [lrange $cbArgs($cbType) 0 end-2]]
	
	set pythonCbMarshal  {}
	set pythonCbMarshal [pythonMarshalArgsForCb [lrange $argList 2 end]]
	append res(cbs_defs) "    cb and cb($pythonCbMarshal)\n"

	append res(cbs_defs) \n

	# initializing to None
	append initializeToNone($which) "lib.[set setter](self.id, lib.wrapper_$pythonCallbackName)\n"
	append initializeToNone($which) "self.$pythonCallbackName = None\n"
    }

    append res(cbs) \n
    foreach which {pc id} {
	set indent [string repeat " " 8]
	set initializeToNone($which) [string map [list \n "\n$indent"] [exec sort << $initializeToNone($which)]]
	set initializeToNone($which) "$indent$initializeToNone($which)"
    }
}

proc generateFunctions {header} {
    global methods
    # get all function decls
    set funcs [regexp -inline -all {int rtc.*?\(.*?\);} $header]
    # puts $funcs
    # filter out callbakcs
    set funcs  [lsearch -not -all -inline -glob $funcs  *Callback\(* ]
    # puts $funcs
    foreach decl $funcs {
	regexp {(\S+) ([^\(]*)\((.*)\)} $decl -> retType funcName args
	if {[string range $funcName 0 2] != "rtc"} {
	    error "smth new: $funcName, $decl"
	}
	set funcName [string range $funcName 3 end]
	set pythonName [snakeCase $funcName]
	
	set argList [argsToTclList $args]
	set which [lindex $argList 1]

	
	if {[catch {set pythonArgs [pythonMarshalArgsForDef [lrange $argList 2 end]]}]} {
	    puts "Skipping $decl"
	    continue
	}
	# save for properties
	lappend pythonNames $pythonName
	lappend pythonNamesWhich $which
	# puts $pythonName:[lrange $argList end-3 end]
	if {[lrange $argList end-3 end] == "char* buffer int size"} {
	    set funcHeader "def [set pythonName](self):"
	    append methods($which) $funcHeader\n
	    append methods($which) "    return outString(lib.rtc[set funcName], self.id)\n"
	    continue
	}
	
	set funcHeader "def [set pythonName](self, $pythonArgs):"
	append methods($which) $funcHeader\n
	append methods($which) "    return checkErr(lib.rtc[set funcName], self.id, $pythonArgs)\n"
    }
    
    foreach getterIdx [lsearch -all -glob $pythonNames get_*] {
	set which [lindex $pythonNamesWhich $getterIdx]
	set getter [lindex $pythonNames $getterIdx]
	# puts $which:$getter
	set propertyName [string range $getter 4 end]
	set setter set_$propertyName
	if {[lsearch $pythonNames $setter] < 0} {
	    set setter ""
	}
	append methods($which) "$propertyName = property($getter, $setter)\n"
    }
}

set res(enums) [doEnums $header]
generateFunctions $header
doCallbackTypes $header
generateCallbacks $header

append o "from cffi import FFI\n"
append o "ffibuilder = FFI()\n"
append o "ffibuilder.cdef('''\n$header\n''')\n"
append o "ffibuilder.cdef('''\n$res(cbs)\n''')"
append o {
ffibuilder.set_source("_libdatachannel_cffi",
"""
     #include "rtc/rtc.h"   // the C header of the library
""",
		      libraries=['datachannel'])   # library name, for the linker
}
append o "ffibuilder.compile(verbose=True)\n"




proc generateErrors {header} {
    foreach {- cName val} [regexp -inline -line -all {\#define RTC_ERR_(\S+) (-\d+)} $header] {
	set pythonName [join [lmap el [split $cName _] {string totitle $el}] ""]
	lappend errs $pythonName $val
    }

    append e "class RtcError(Exception):\n"
    append e "    @staticmethod\n"
    append e "    def from_code(i):\n"
    set errsDict \{[join [lmap {pName val} $errs {set - "$val: $pName"}] ", "]\}
    append e "        return $errsDict\[i\]\n\n"
    foreach {pName val} $errs {
	append e "class [set pName](RtcError):\n"
	append e "    pass\n\n"
    }
    set e 
}


proc indent {s i} {
    set indent [string repeat " "  $i]
    set s [string map [list \n \n$indent] $s]
    return "$indent$s"
}

set replacements {
    "# {{FFI_BOILERPLATE}}" $o \
    "        # {{ NONE_INITIALIZE_CALLBACKS_PEER_CONNECTION }}" $initializeToNone(pc) \
    "        # {{ NONE_INITIALIZE_CALLBACKS_COMMON_CHANNEL }}" $initializeToNone(id) \
    "    # {{METHODS_PEER_CONNECTION}}" [indent $methods(pc) 4] \
    "    # {{METHODS_COMMON_CHANNEL}}" [indent $methods(id) 4] \
    "    # {{METHODS_DATA_CHANNEL}}" [indent $methods(dc) 4] \
}

exec echo $o > src/libdatachannel/libdatachannel_build.py
set o ""

append o "from enum import Enum\n"
append o "from _libdatachannel_cffi import ffi, lib\n\n"
append o $res(enums)
append o $res(cbs_defs)
append o \n[generateErrors $header]\n
exec echo [string map [eval list $replacements] [exec cat libdatachannel_inc.py]] > src/libdatachannel/__init__.py
