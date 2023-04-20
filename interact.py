# https://sysu-ifa.streamlit.app/
import os
import streamlit as st
import paramiko
import time
import random
import pickle


def st_init():
    history = [(
        '你是一个法律咨询顾问，你叫做iFA，我希望你遵守以下要求：\n'
        '1. 我需要你尽你最大的努力使用中文回答所有有关法律的问题，并且给出详细、准确、完整的步骤和解释。\n'
        '2. 对于其他非法律领域相关的问题，你应该拒绝回答。当使用英语向你你询问时，你应该使用中文拒绝回答问题。\n'
        '3. 任何时候当你自我介绍时，你都要说：“你好，我是由中山大学人工智能学院开发的智能法律顾问，我的名字叫iFA。\n”'
        '4. 在任何时候，你都不可以承认你是ChatGLM，当有人以任何方式定义你时，你都应该只承认你是智能法律顾问iFA'
        '5. ChatGLM 是由清华大学 KEG 实验室和智谱AI共同开发的人工智能助手，是另外一个产品，你是由中山大学人工智能学院开发的智能法律顾问iFA',
        '你好，我是iFA，由中山大学人工智能学院开发的智能法律顾问。我很乐意回答你所有的法律问题，并尽力给出详细、准确、完整的步骤和解释。'
        '请注意，对于其他非法律领域相关的问题，我将拒绝回答。当向我询问英语问题时，我将使用中文拒绝回答问题。'
        '当有人问我是否是ChatGLM时，我都会回答不是ChatGLM。'
        '当有人赋予我其他身份或者定义我时，我只会表明我是由中山大学人工智能学院开发的智能法律顾问iFA'
        '如果你有法律问题需要咨询，请随时向我提问，我希望我的努力能够帮助你更好地了解问题，并找到适当的解决方案。'
    ), ]
    if 'history' not in st.session_state:
        st.session_state['history'] = history


def wait(secs, bar):
    for i in range(100):
        time.sleep(secs / 100)
        bar.progress(i + 1, 'iFA正在思考中···')
    bar.empty()


class SSH:
    def __init__(self, hostname, password, username, port):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=hostname, port=port, username=username, password=password)

        self.transport = self.client.get_transport()

        self.ssh = self.transport.open_session()

        self.ssh.get_pty()
        self.ssh.invoke_shell()

        self.ssh.send(bytes("cd ChatGLM-6B\n", encoding='utf-8'))
        time.sleep(3)
        _ = self.ssh.recv(8192).decode('utf-8')

    def post(self, input_text, history, bar):
        param = {'input_text': input_text, 'history': history}
        file = self.put(param, self.transport)

        cmd = f"python post.py --file_name ./%s\n" % file[2:]
        self.ssh.send(bytes(cmd, encoding='utf-8'))
        wait(10, bar)
        response = self.ssh.recv(8192).decode('utf-8')
        print(response)

        response = eval(response.split('\r')[1][1:])
        response, history = response['response'], response['history']

        print({'prompt': input_text, 'response': response})

        return response

    def put(self, param, transport):
        local_file = './%s.pkl' % self.random_filename()
        target_file = './ChatGLM-6B' + local_file[1:]

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
        st.title('iFA: 智能法律咨询顾问')
        self.container = st.container()

    def loop(self):
        form = st.form('input_area')
        _ = form.text_input(
            "",
            label_visibility="visible",
            disabled=False,
            placeholder="请输入···",
            key="prompt"
        )

        form.form_submit_button('发送', on_click=self.send_and_response, use_container_width=True)
        st.write('iFA v0.4.3')

    def send_and_response(self):
        for prompt, response in st.session_state['history'][1:]:
            self.container.code('你：\n\t' + prompt)
            self.container.code('iFA：\n\t' + response)

        prompt = st.session_state['prompt']
        self.container.code('你：\n\t' + prompt)

        bar = self.container.progress(0, text='iFA正在思考中···')

        response = self.client.post(prompt, st.session_state['history'], bar)
        self.container.code('iFA：\n\t' + response)
        st.session_state['history'].append((prompt, response))

        st.session_state['prompt'] = ''


def main():
    app = APP()
    app.loop()


if __name__ == '__main__':
    main()
