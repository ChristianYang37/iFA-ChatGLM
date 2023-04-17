# https://sysu-ifa.streamlit.app/
import os
import streamlit as st
import paramiko
import time
import random
import pickle


def st_init():
    if 'prompts' not in st.session_state:
        st.session_state['prompts'] = []
    if 'responses' not in st.session_state:
        st.session_state['responses'] = []


class SSH:
    def __init__(self, hostname, password, username, port):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=hostname, port=port, username=username, password=password)

    def post(self, input_text, history):
        transport = self.client.get_transport()

        ssh = transport.open_session()

        ssh.get_pty()
        ssh.invoke_shell()

        ssh.send(bytes("cd ChatGLM-6B\n", encoding='utf-8'))
        time.sleep(3)
        _ = ssh.recv(8192)

        param = {'input_text': input_text, 'history': history}
        file = self.put(param, transport)

        cmd = f"python post.py --file_name ./tmp/%s\n" % file[2:]
        ssh.send(bytes(cmd, encoding='utf-8'))
        time.sleep(30)
        response = ssh.recv(8192).decode('utf-8')

        print(response)

        response = eval(response.split('\r')[1][1:])
        response, history = response['response'], response['history']

        return response

    def put(self, param, transport):
        local_file = './%s.pkl' % self.random_filename()
        target_file = './ChatGLM-6B/tmp' + local_file[1:]

        with open(local_file, mode='wb') as file:
            pickle.dump(param, file, True)

        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put(local_file, target_file)

        os.remove(local_file)

        return local_file

    vocab = [chr(i) for i in range(48, 58)] + [chr(i) for i in range(65, 91)] + [chr(i) for i in range(97, 123)]

    def random_filename(self, ):
        length = 16
        s = ''
        for _ in range(length):
            s += random.choice(self.vocab)
        return s


class APP:
    def __init__(self):
        st_init()
        self.client = SSH(st.secrets['hostname'], st.secrets['password'], st.secrets['username'], st.secrets['port'])
        st.title('iFA: 你的智能法律咨询顾问')
        self.container = st.container()

    def loop(self):
        form = st.form('input_area')
        input_text = form.text_input(
            "",
            label_visibility="visible",
            disabled=False,
            placeholder="Just Type...",
            key="text"
        )
        print(input_text)

        form.form_submit_button('发送', on_click=self.send_and_response, use_container_width=True)

    def send_and_response(self):
        text = st.session_state['text']
        st.session_state['prompts'].append(text)
        history = [[prompt, response] for prompt, response in
                   zip(st.session_state['prompts'], st.session_state['responses'])]
        st.session_state['responses'].append(self.client.post(text, history)[0])

        for prompt, response in zip(st.session_state['prompts'], st.session_state['responses']):
            self.container.code('你：\n\t' + prompt)
            self.container.code('iFA：\n\t' + response)

        st.session_state['text'] = ''


def main():
    app = APP()
    app.loop()


if __name__ == '__main__':
    main()
