# https://sysu-ifa.streamlit.app/
import streamlit as st
import paramiko
import time
import random
import pickle

vocab = [chr(i) for i in range(48, 58)] + [chr(i) for i in range(65, 91)] + [chr(i) for i in range(97, 123)]


def random_filename():
    length = 8
    s = ''
    for _ in range(length):
        s += random.choice(vocab)
    return s


class SSH:
    def __init__(self, hostname, password, username, port):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=hostname, port=port, username=username, password=password)
        self.file = './%s.pkl' % random_filename()
        self.target_file = './ChatGLM-6B' + self.file[1:]

    def post(self, input_text, history):
        transport = self.client.get_transport()

        ssh = transport.open_session()

        ssh.get_pty()
        ssh.invoke_shell()

        ssh.send(bytes("cd ChatGLM-6B\n", encoding='utf-8'))
        time.sleep(10)
        _ = ssh.recv(8192)

        param = {'input_text': input_text, 'history': history}
        self.put(param, transport)

        cmd = f"python post.py --file_name %s\n" % self.file
        ssh.send(bytes(cmd, encoding='utf-8'))
        time.sleep(10)
        response = ssh.recv(8192)

        print(response.decode('utf-8'))

        response = eval(response.decode('utf-8').split('\r')[1][1:])
        response, history = response['response'], response['history']

        return response, history

    def put(self, param, transport):
        with open(self.file, mode='wb') as file:
            pickle.dump(param, file, True)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(self.file, self.target_file)

    def __del__(self):
        pass
        # transport = self.client.get_transport()
        #
        # ssh = transport.open_session()
        #
        # ssh.get_pty()
        # ssh.invoke_shell()
        #
        # ssh.send(bytes("rm -rf %s\n" % self.target_file, encoding='utf-8'))
        # os.system("rm -rf %s\n" % self.file)
        # self.client.close()


class APP:
    txt = ''

    def __init__(self):
        self.client = SSH(st.secrets['hostname'], st.secrets['password'], st.secrets['username'], st.secrets['port'])
        # st.title('iFA: 你的智能法律咨询顾问')
        st.title('Chat with ChatGLM-6B!')

    def loop(self):
        chat_state = {'LoopTimeCount': 0, 'GetInput': True, 'History': []}
        while True:
            chat_state = self.interact(**chat_state)

    def interact(self, LoopTimeCount, GetInput, History):
        input_text = ''
        if GetInput:
            input_text = st.text_input('', key=LoopTimeCount)
        if input_text:
            print(input_text, History)
            response, History = self.client.post(input_text, History)

            st.code(response)

            del input_text
        else:
            GetInput = False
        return {'LoopTimeCount': LoopTimeCount + 1, 'GetInput': GetInput, 'History': History}


if __name__ == '__main__':
    app = APP()
    app.loop()
