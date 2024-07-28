import sys

sys.path.append('..')


def my_function():
    # Do some work here
    my_function.custom_attribute = 'Hello, World!'


# Call the function to set the attribute
my_function()

# Access the function attribute
print(my_function.custom_attribute)  # Output: Hello, World!


def aas(s: str, i: int) -> str:
    sss: str = 'asdf' + s
    dss: dict = {
        sss: 1,
        'b': 2
    }
    aas.abc = 'ab'
    print('aa')
    asdfa = '''
sdf, asdf sd = [sdfs] asdf
sdf
sdfasdf
'''
    return 'aasd' + s + str(i) + sss


aas('asdf', 1)

print(aas.abc)
aas