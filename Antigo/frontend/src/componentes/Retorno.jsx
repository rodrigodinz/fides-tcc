import { useCallback, useEffect, useRef, useState } from "react";
import { ContextoToast } from "./toast.js";
import Icone from "./Icone.jsx";
import { Botao } from "./Botao.jsx";
import { prenderFoco } from "./focoPreso.js";

/* ---------------- toast: retorno breve de ações locais ---------------- */

export function ProvedorToast({ children }) {
  const [itens, setItens] = useState([]);
  const avisar = useCallback((texto) => {
    const id = Date.now() + Math.random();
    setItens((l) => [...l.slice(-2), { id, texto }]);
    setTimeout(() => setItens((l) => l.filter((t) => t.id !== id)), 3200);
  }, []);
  return (
    <ContextoToast.Provider value={avisar}>
      {children}
      <div className="fd-toasts" role="status" aria-live="polite">
        {itens.map((t) => <div key={t.id} className="fd-toast"><Icone nome="check" />{t.texto}</div>)}
      </div>
    </ContextoToast.Provider>
  );
}

/* ---------------- modal: só para confirmações que não têm volta ---------------- */
export function Confirmacao({ aberto, titulo, children, confirmar = "Confirmar", cancelar = "Cancelar", aoConfirmar, aoCancelar }) {
  const ref = useRef(null);
  const refCancelar = useRef(null);
  useEffect(() => {
    if (!aberto) return undefined;
    const anterior = document.activeElement;
    refCancelar.current?.focus();
    const tecla = (e) => { if (e.key === "Escape") aoCancelar(); else prenderFoco(e, ref.current); };
    document.addEventListener("keydown", tecla);
    return () => { document.removeEventListener("keydown", tecla); anterior?.focus?.(); };
  }, [aberto, aoCancelar]);
  if (!aberto) return null;
  return (
    <div className="fd-modal-veu" onClick={(e) => { if (e.target === e.currentTarget) aoCancelar(); }}>
      <div ref={ref} className="fd-modal" role="alertdialog" aria-modal="true" aria-labelledby="fd-modal-titulo" aria-describedby="fd-modal-texto">
        <h2 id="fd-modal-titulo" className="fd-h4">{titulo}</h2>
        <div id="fd-modal-texto" style={{ marginTop: 8 }}>{children}</div>
        <div className="fd-modal__acoes">
          <Botao ref={refCancelar} variante="secundario" onClick={aoCancelar}>{cancelar}</Botao>
          <Botao variante="especial" onClick={aoConfirmar}>{confirmar}</Botao>
        </div>
      </div>
    </div>
  );
}
