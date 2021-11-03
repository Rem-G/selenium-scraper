import configparser
config = configparser.ConfigParser()
config['BRIGHTDATA'] = {'brightdata_username': '',
                      'brightdata_pwd': ''}

with open('credentials.ini', 'w') as configfile:
   config.write(configfile)