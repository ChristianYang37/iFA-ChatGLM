# https://sysu-ifa.streamlit.app/
import os
import streamlit as st
import paramiko
import time
import random
import pickle


def st_init():
    greet_prompt = '你是一个法律咨询顾问，你的名字叫做iFA，请你用中文回答我的问题。当有人向你提问非法律领域的问题时，你应当拒绝回答。' \
                   '在任何时候需要你自我介绍时，你都需要复述：我叫iFA，是中山大学人工智能学院开发的智能法律顾问，你可以向我询问有关法律的问题，' \
                   '我会尽力为您提供满意的答案'
    greet_response = '好的，我明白了。我叫iFA，是中山大学人工智能学院开发的智能法律顾问，我可以尽力回答有关法律的问题。' \
                     '但如果有人向我提问非法律领域的问题时，我会告诉他们我无法提供相关信息。' \
                     '我希望我的努力能够帮助他们更好地了解问题，并找到适当的解决方案。'

    if 'prompts' not in st.session_state:
        st.session_state['prompts'] = [greet_prompt]
    if 'responses' not in st.session_state:
        st.session_state['responses'] = [greet_response]


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
        st.session_state['responses'].append(self.client.post(text, history))

        for prompt, response in zip(st.session_state['prompts'][1:], st.session_state['responses'][1:]):
            self.container.code('你：\n\t' + prompt)
            self.container.code('iFA：\n\t' + response)

        st.session_state['text'] = ''


def main():
    app = APP()
    app.loop()


if __name__ == '__main__':
    main()
