"use client";
import { Button, Card, Form, Input } from 'antd';
import styles from './styles.module.scss';

export default function Page() {
    return (
        <div
            className={styles['login']}
        >
            <Card
                variant='borderless'
                className={styles['login-card']}
            >
                <Form
                    onFinish={(data) => console.log(data)}
                    layout='vertical'
                >
                    <Form.Item
                        style={FormItemStyle}
                    >
                        <span
                            style={TextStyle}
                        >
                            Авторизация
                        </span>
                    </Form.Item>
                    <Form.Item
                        name="login"
                        label="Логин"
                    >
                        <Input
                            placeholder='Введите логин'
                            allowClear
                        />
                    </Form.Item>
                    <Form.Item
                        name="password"
                        label="Пароль"
                    >
                        <Input.Password
                            placeholder='Введите пароль'
                            allowClear
                        />
                    </Form.Item>
                    <Form.Item
                        style={FormItemStyle}
                    >
                        <Button
                            htmlType='submit'
                            type='primary'
                        >
                            Войти
                        </Button>
                    </Form.Item>
                </Form>
            </Card>
        </div>
    )
}


const FormItemStyle: React.CSSProperties = {
    textAlign: "center"
}

const TextStyle: React.CSSProperties = {
    fontSize: "1.25rem",
    fontWeight: 600
}