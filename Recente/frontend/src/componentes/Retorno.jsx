import { useCallback, useEffect, useRef, useState } from "react";
import { ContextoToast } from "./toast.js";
import Icone from "./Icone.jsx";
import { Botao } from "./Botao.jsx";
import { prenderFocoNoContainer } from "./focoPreso.js";

const Tempo_Do_Aviso_Na_Tela = 3200;

// avisos rápidos (toast) que somem sozinhos em 3,2 s; o Provider deixa qualquer componente chamar avisar()
export function ProvedorToast({ children }) {
  const [avisosNaTela, setAvisosNaTela] = useState([]);
  const avisar = useCallback((texto) => {
    const idDoAviso = Date.now() + Math.random();
    setAvisosNaTela((avisosAnteriores) => [...avisosAnteriores.slice(-2), { id: idDoAviso, texto }]);
    setTimeout(() => setAvisosNaTela((avisosAtuais) => avisosAtuais.filter((aviso) => aviso.id !== idDoAviso)), Tempo_Do_Aviso_Na_Tela);
  }, []);
  return (
    <ContextoToast.Provider value={avisar}>
      {children}
      <div className="fd-toasts" role="status" aria-live="polite">
        {avisosNaTela.map((aviso) => <div key={aviso.id} className="fd-toast"><Icone nome="check" />{aviso.texto}</div>)}
      </div>
    </ContextoToast.Provider>
  );
}

// janela de confirmação (modal); Esc cancela e o foco fica preso dentro dela enquanto está aberta
export function Confirmacao({ aberto, titulo, children, textoConfirmar = "Confirmar", textoCancelar = "Cancelar", aoConfirmar, aoCancelar }) {
  const referenciaDoModal = useRef(null);
  const referenciaDoBotaoCancelar = useRef(null);
  useEffect(() => {
    if (!aberto) return undefined;
    const elementoFocadoAntes = document.activeElement;
    referenciaDoBotaoCancelar.current?.focus();
    const aoPressionarTecla = (evento) => {
      if (evento.key === "Escape") aoCancelar();
      else prenderFocoNoContainer(evento, referenciaDoModal.current);
    };
    document.addEventListener("keydown", aoPressionarTecla);
    return () => { document.removeEventListener("keydown", aoPressionarTecla); elementoFocadoAntes?.focus?.(); };
  }, [aberto, aoCancelar]);
  if (!aberto) return null;
  return (
    <div className="fd-modal-veu" onClick={(evento) => { if (evento.target === evento.currentTarget) aoCancelar(); }}>
      <div ref={referenciaDoModal} className="fd-modal" role="alertdialog" aria-modal="true" aria-labelledby="fd-modal-titulo" aria-describedby="fd-modal-texto">
        <h2 id="fd-modal-titulo" className="fd-h4">{titulo}</h2>
        <div id="fd-modal-texto" style={{ marginTop: 8 }}>{children}</div>
        <div className="fd-modal__acoes">
          <Botao ref={referenciaDoBotaoCancelar} variante="secundario" onClick={aoCancelar}>{textoCancelar}</Botao>
          <Botao variante="especial" onClick={aoConfirmar}>{textoConfirmar}</Botao>
        </div>
      </div>
    </div>
  );
}
