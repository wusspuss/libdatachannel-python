import re
from collections import defaultdict


methods_blacklist=['rtcSendMessage']
def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

with open('/usr/include/rtc/rtc.h', 'r') as f:
    header = f.read()

skipped=[] # lists all function we skipped auto-generating 

# collect just the enums from the header
enums_header='\n'.join(
    re.findall(r'typedef enum[^;]*;', header, re.DOTALL)
)
# collect just the structs from the header
structs_header='\n'.join(
    re.findall(r'typedef struct.*?}.*?;', header, re.DOTALL)
)

# collect just the callbacks from the header
callbacks_header='\n'.join(
    re.findall(r'typedef void.*?;', header, re.DOTALL)
).replace("RTC_API", "")

# collect just the function definitions from the header
funcs_header_lines = re.findall(r'\nRTC_C_EXPORT (.*?;)', header, re.DOTALL)
funcs_header='\n'.join(
    funcs_header_lines
)

# we break up rtc.h functions into class methods
# rtc.h is pretty consistent: a "method" always takes an int arg with the arg name \
# corresponding to the "class"
# so tr -> Track, dc -> DataChannel, pc -> PeerConnection
# methods taking arg called "id" are common to Track and DataChannel, \
# so we'll shove those into "CommonChannel" and have those two inherit from it

class_methods={'tr':[], 'dc': [], 'pc': [], 'id': [], 'ws': []}

for line in funcs_header_lines:
    try:
        c_func_name = re.findall(r"int (rtc[^\(]*)",line)[0]
    except IndexError:
        skipped.append(line)
        continue
    if c_func_name in methods_blacklist:
        continue
    if c_func_name.endswith('Callback'):
        continue
    # make "char *s" into "char* s"
    # so we can later break it up into a list like [["type", "arg"], ...]
    line=line.replace(" *", "* ")\
             .replace("const ", "")\
             .replace('\n', ' ')\
             .replace('unsigned','')
    line=re.sub(r'\s+', ' ', line)
    # extract what's between braces
    inside_c_braces = re.findall(r"\((.*?)\)", line, re.DOTALL)[0]
    if inside_c_braces=='void':
        skipped.append(line)
        continue
    args=[arg_pair_str.split(' ') for arg_pair_str in inside_c_braces.split(', ')]
    pythonic_name=camel_to_snake(c_func_name[3:])
    
    if args[1:]==[['char*', 'buffer'], ['int','size']]:        
        class_methods[args[0][1]].append(''.join([
            '    ', f"def {pythonic_name}(self):\n"
            '    ', '    ',  f'return outString(lib.{c_func_name}, self.id)'
        ]))
        continue

    if c_func_name in ['rtcReceiveMessage', 'rtcGetSelectedCandidatePair', ]:
        skipped.append(line)
        continue
    python_args='' # what goes in def ...(???)
    type_annotation={'char*': 'str', 'int':'int'}

    
    if args[0][0] == 'int' and args[0][1] in class_methods.keys():
        try:
            python_def_args=', '.join([f'{name}: {type_annotation[type_]}' for (type_, name) in args[1:]])
        except KeyError:
            skipped.append(line)
            continue
        python_calling_args=re.sub('char\* ([^,]*)', r'\1.encode()', inside_c_braces[8:]).replace('int ', '')
        class_methods[args[0][1]].append(''.join([
            '    ', f"def {pythonic_name}(self, {python_def_args}):\n"
            '    ', '    ', f'return checkErr(lib.{c_func_name}, self.id, {python_calling_args})'
        ]))
    
class_methods={k:'\n'.join(v) for k,v in class_methods.items()}

# enums
python_enums=[]
enum_names=[] # for checking in callbacks code
for enum in re.findall(r'typedef enum[^;]*;', enums_header.replace('\t',''), re.DOTALL):
    enum_name=re.findall(r'rtc(\S+);$', enum)[0]
    enum_names.append(enum_name)
    python_enums.append(f'class {enum_name}(IntEnum):\n')
    for name, value in (re.findall(r'RTC_(.*?) = (.*?)[,\n]', enum)):
        python_enums.append(f'    {name} = {value}\n')
    python_enums.append('\n')

python_enums=''.join(python_enums)

callback_typedefs_info={}

# First parse callback typedefs, figure out what arguments to pass to them
# then parse callback setters
for cb_name, cb_args in re.findall(r'(rtc.*?CallbackFunc)\)\((.*?)\)', callbacks_header, re.DOTALL):
    callback_typedefs_info[cb_name]={}
    python_cb_marshaller=[]
    # e.g. "rtcLogLevel level, const char *message" -> [['rtcLogLevel', 'level'], ['char*', 'message']]
    cb_args=re.sub(r'\s+', ' ', cb_args)
    callback_typedefs_info[cb_name]['cb_args']=cb_args
    cb_args = [arg_pair.split() for arg_pair in cb_args\
               .replace(' *', '* ')\
               .replace('const', '')\
               .split(', ')]
    cb_class=None
    callback_typedefs_info[cb_name]['python_args']=', '.join([name for type_,name in cb_args])
    if cb_args[0][0]=='int' and cb_args[0][1] in ['tr','id','pc']:
        cb_class=cb_args[0][1]
        cb_args=cb_args[1:]
        
    for type_, name in cb_args:
        if type_=='int' and name in ['tr', 'dc']:
            python_class = {'tr': 'Track', 'dc': 'DataChannel'}[name]
            python_cb_marshaller.append(f'{python_class}.get_by_id({name}), ')
        elif type_=='char*':
            python_cb_marshaller.append(f'ffi.string({name}).decode(), ')
        elif type_[3:] in enum_names:
            python_cb_marshaller.append(f'{type_[3:]}({name}), ')
    python_cb_marshaller=''.join(python_cb_marshaller)

    
    callback_typedefs_info[cb_name]['class']=cb_class
    callback_typedefs_info[cb_name]['marshaller']=python_cb_marshaller

callback_setters_per_class=defaultdict(list)
python_callback_wrappers=[]
callback_cdefs=[]
# callbacks
for (callback_setter, cb_type) in re.findall(r'int (rtcSet.*Callback)\(int .., (\S+)', funcs_header):
    if callback_setter=='rtcSetMediaInterceptorCallback':
        # special case - can't generate automatically
        continue
    # goes like: rtcSetLocalDescriptionCallback rtcDescriptionCallbackFunc
    cb_name=camel_to_snake(callback_setter[6:])
    typedef_info=callback_typedefs_info[cb_type]
    # goes like ('rtcSetLocalDescriptionCallback', 'pc', 'rtcDescriptionCallbackFunc')
    python_callback_name = camel_to_snake(callback_setter[6:])
    python_callback_wrappers.append("@ffi.def_extern()\n")
    python_callback_wrappers.append(f"def wrapper_{python_callback_name}({typedef_info['python_args']}):\n")

    cls_names={'pc': 'PeerConnection', 'id': 'CommonChannel'}
    callback_setters_per_class[typedef_info['class']].append(callback_setter)
    python_callback_wrappers.append('    ')
    python_callback_wrappers.append(f'cb = {cls_names[typedef_info["class"]]}')
    python_callback_wrappers.append(f'.get_by_id({typedef_info["class"]})')
    python_callback_wrappers.append(f'.{cb_name}\n')
    python_callback_wrappers.append('    ')
    python_callback_wrappers.append(f'cb and threadsafe_scheduler(cb, {typedef_info["marshaller"]})\n\n')

    # cdef
    callback_cdefs.append(f'extern "Python" void wrapper_{python_callback_name}({typedef_info["cb_args"]});\n')

callback_cdefs = '\n'.join(callback_cdefs)
cdef_input='\n'.join([enums_header, structs_header, callbacks_header, funcs_header, callback_cdefs])
python_callback_wrappers = ''.join(python_callback_wrappers)

for class_ in class_methods:
    for property_ in re.findall('def get_(.*)\(', class_methods[class_]):
        if re.findall(f'def set_{property}\(', class_methods[class_]):
            class_methods[class_]+=f'\n    {property_} = property(get_{property_}, set_{property_})'
        else:
            class_methods[class_]+=f'\n    {property_} = property(get_{property_})'

callback_none_init_per_class={}

for class_, callback_setters in callback_setters_per_class.items():
    callback_none_init_per_class[class_]=[]
    for callback_setter in callback_setters:
        python_callback_name = camel_to_snake(callback_setter[6:])
        callback_none_init_per_class[class_].append(f'        lib.{callback_setter}(self.id,'
                                                    f'lib.wrapper_{python_callback_name})\n'
                                                    f'        self.{python_callback_name}=None\n')
    callback_none_init_per_class[class_]=''.join(callback_none_init_per_class[class_])

python_callback_name = camel_to_snake(callback_setter[6:])

with open('libdatachannel_inc.py', 'r') as f:
    template = f.read()

template=template.replace('# {{METHODS_COMMON_CHANNEL}}', class_methods['id']) \
                 .replace('# {{METHODS_DATA_CHANNEL}}', class_methods['dc'],) \
                 .replace('# {{METHODS_TRACK}}', class_methods['tr'],) \
                 .replace('# {{METHODS_PEER_CONNECTION}}', class_methods['pc'],) \
                 .replace('# {{ENUMS}}', python_enums,) \
                 .replace('# {{PYTHON_CALLBACK_WRAPPERS}}', python_callback_wrappers) \
                 .replace('# {{ NONE_INITIALIZE_CALLBACKS_PEER_CONNECTION }}', callback_none_init_per_class['pc'])\
                 .replace('# {{ NONE_INITIALIZE_CALLBACKS_COMMON_CHANNEL }}', callback_none_init_per_class['id'])

with open("src/libdatachannel/__init__.py", "w") as f:
    f.write(template)

with open("src/libdatachannel/libdatachannel_build.py", "w") as f:
    f.write('''
from cffi import FFI
ffibuilder = FFI()
ffibuilder.cdef("""
#{{CDEF_INPUT}}
""")
ffibuilder.set_source("_libdatachannel_cffi",
"""
     #include "rtc/rtc.h"   // the C header of the library
""",
		      libraries=['datachannel'])   # library name, for the linker
ffibuilder.compile(verbose=True)
'''.replace("#{{CDEF_INPUT}}", cdef_input))
print('\n    '.join(["Skipped auto-generating the following methods:"]+skipped), sep='')


