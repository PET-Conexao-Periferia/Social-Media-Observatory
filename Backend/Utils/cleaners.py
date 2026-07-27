import re

def clean_text(txt, user=None, legenda_text=None):
                                if not txt:
                                    return txt
                                t = txt
                                # remover ocorrências repetidas do username no início/fim
                                if user:
                                    try:
                                        uname = user.strip()
                                        # remover quando aparece seguido de espaços/novas linhas
                                        t = re.sub(
                                            r"(?i)^" + re.escape(uname) + r"[\s:-]*", "", t)
                                        t = re.sub(
                                            r"(?i)[\s:-]*" + re.escape(uname) + r"$", "", t)
                                    except Exception:
                                        pass
                                # remover tokens comuns de UI
                                t = re.sub(
                                    r"(?i)\b(responder|respostas?|ver todas( as)?( as)?|editar|editado|reply)\b", "", t)
                                # remover marcações de tempo como '3 sem', '1 h', '2d', '3w', 'ago'
                                t = re.sub(
                                    r"\b\d+\s*(sem|h|m|d|w|mes(es)?|ano(s)?|s|min)\b", "", t)
                                t = re.sub(
                                    r"\b(\d+)\s*curtid[ao]s?\b", "", t, flags=re.I)
                                # remover palavras soltas como 'Curtir', 'Responder', 'Curtir\n'
                                t = re.sub(
                                    r"(?i)\b(Curtir|Curtir|Curtir\n|Curtir )\b", "", t)
                                # remover pontos de separação e bullets soltos
                                t = t.replace('•', ' ')
                                # remover múltiplas quebras de linha e espaços extras
                                t = re.sub(r"\n{2,}", "\n", t)
                                t = re.sub(r"[ ]{2,}", " ", t)
                                return t.strip()

                            comment_text = clean_text(
                                comment_text, username, legenda)
                    except Exception:
                        comment_text = None
