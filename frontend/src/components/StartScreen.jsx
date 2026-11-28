import { useEditor } from '../editor/EditorContext.jsx'

const StartScreen = () => {
  const { openInput, apiError } = useEditor()
  return (
    <div className='flex flex-1 items-center justify-center p-6'>
      <div className='flex max-w-lg flex-col items-center gap-4 rounded border border-gray-400 bg-white p-8 text-center shadow'>
        <h2 className='text-xl font-bold text-blue-800'>Nincs betöltött bánya</h2>
        <p className='text-gray-600'>
          Nyisd meg a bemeneti fájlt: ez tartalmazza a bánya térképét és a MineScript programot.
          A robot beállításait (akkumulátor, energiaigények) a ⚙ Beállítások gombbal adhatod meg.
        </p>
        <button onClick={openInput}
          className='rounded bg-blue-700 px-4 py-2 font-semibold text-white hover:bg-blue-800'>
          📂 Bemenet megnyitása…
        </button>
        <p className='text-sm text-gray-500'>
          A napló alapértelmezés szerint a bemenet mellé kerül <code>output.txt</code> néven.
          A helyét a fejlécben, a „Napló helye…” gombbal bármikor megváltoztathatod.
        </p>
        {apiError && <p className='text-sm text-red-600'>Backend hiba: {apiError}</p>}
      </div>
    </div>
  )
}

export default StartScreen
