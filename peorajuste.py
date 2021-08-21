import random
from enum import Enum

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.clock import Clock

TIME=1
PROCESOS=30

class Status(Enum):
    ESPERA=1
    CARGADO=2
    TERMINADO=3
    OCUPADA=4
    LIBRE=5

class RVProcesos(RecycleView):
    procesos=[]
    def __init__(self, **kwargs):
        super(RVProcesos, self).__init__(**kwargs)
        for i in range(PROCESOS):
            proceso_memoria=random.randrange(500,5000)
            texto='Proceso '+ str(i+1)+' ('+str(proceso_memoria)+'KB)'
            duracion=random.randint(2,8)
            proceso=Proceso(i+1, texto, proceso_memoria, duracion)
            self.procesos.append(proceso)
            self.data.append({'id': proceso.id, 'text': proceso.text})


class RV(RecycleView):
    procesos=[]
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data=[]

    def agregar_espera(self, proceso):
        self.procesos.append(proceso)
        self.data.append({'id': proceso.id, 'text': proceso.text, 'color': [1,1,1,1]})

    def agregar_particion(self, particiones):
        self.data=[]
        for particion in particiones:
            if particion['status']==Status.LIBRE:
                texto='Libre. '+str(particion['memoria'])+' (KB)'
                self.data.append({'id': particion['inicio'], 'text': texto, 'color': [0,1,0,1]})
            else:
                texto='Ocupada. '+str(particion['memoria'])+' (KB)'
                self.data.append({'id': particion['inicio'], 'text': texto, 'color': [1,0,0,1]})

class Proceso(Label):
    status=Status.ESPERA
    inicio_fin=tuple()
    remover_callback=None
    def __init__(self, proceso_id, texto, memoria, duracion, **kwargs):
        super(Proceso, self).__init__(**kwargs)
        self.id=proceso_id
        self.text=texto
        self.memoria=memoria
        self.duracion=duracion

    def asignar_particion(self, inicio_fin, remover_callback):
        self.inicio_fin=inicio_fin
        self.status=Status.CARGADO
        self.remover_callback=remover_callback
        Clock.schedule_once(self.remover_proceso, self.duracion)

    def remover_proceso(self, *args):
        if callable(self.remover_callback):
            self.remover_callback(self)


class MemoriaLabel(Label):
    def __init__(self, memoria_total, size_hint, pos_hint, **kwargs):
        super(MemoriaLabel, self).__init__(**kwargs)
        self.text='Memoria Total: ' + memoria_total
        self.size_hint=size_hint
        self.pos_hint=pos_hint


class MemoriaPrincipal(FloatLayout):
    memoria_total=random.randint(10,20)*1000
    memoria_libre=memoria_total*.9
    particiones=[{'inicio': 1,'fin': .9, 'memoria': memoria_total*.1, 'status': Status.OCUPADA}, {'inicio': .9, 'fin': 0, 'memoria': memoria_total*.9, 'status': Status.LIBRE}]
    agregar_espera=None
    agregar_particion=None
    def __init__(self, **kwargs):
        super(MemoriaPrincipal, self).__init__(**kwargs)
        memoria_label=MemoriaLabel(str(self.memoria_total)+'KB', (1, .1),
                {'x':0, 'y':.9})
        self.add_widget(memoria_label)  

    def primer_ajuste(self, proceso):
        change=False
        particion_temp=self.particiones.copy()
        for index, particion in enumerate(self.particiones):
            if particion['status']==Status.LIBRE and particion['memoria']>=proceso.memoria:
                if particion['memoria']==proceso.memoria:
                    particion['status']==Status.OCUPADA
                    self.add_widget(proceso)
                else:
                    height=proceso.memoria/self.memoria_total
                    proceso.size_hint=(1,height)
                    pos_y=(particion['inicio']-height)
                    proceso.asignar_particion((particion['inicio'], pos_y), self.desasignacion)
                    proceso.pos_hint={'x':0, 'y': pos_y}
                    nueva_libre={'inicio':pos_y, 'fin': particion['fin'], 'memoria':particion['memoria']-proceso.memoria, 'status': Status.LIBRE}
                    particion_temp.pop(index)
                    particion_temp.insert(index, {'inicio': proceso.inicio_fin[0], 'fin': proceso.inicio_fin[1], 'memoria': proceso.memoria, 'status': Status.OCUPADA})
                    particion_temp.insert(index+1, nueva_libre)
                    self.add_widget(proceso)
                change=True
                break
        if change:
            self.particiones.clear()
            self.particiones=particion_temp.copy()
            if callable(self.agregar_particion):
                self.agregar_particion(self.particiones)
        else:
            if callable(self.agregar_espera):
                self.agregar_espera(proceso)

    def peor_ajuste(self, proceso):
        particion_temp=self.particiones.copy()
        initial_memory_waste=-1
        subscript=0
        for index, particion in enumerate(self.particiones):
            if particion['status']==Status.LIBRE and particion['memoria']>=proceso.memoria:
                memory_waste=particion['memoria']-proceso.memoria
                if memory_waste>initial_memory_waste:
                    subscript=index
                    initial_memory_waste=memory_waste
        if subscript==0:
            if callable(self.agregar_espera):
                self.agregar_espera(proceso)
        else:
            height=proceso.memoria/self.memoria_total
            proceso.size_hint=(1,height)
            pos_y=(self.particiones[subscript]['inicio']-height)
            proceso.asignar_particion((self.particiones[subscript]['inicio'], pos_y), self.desasignacion)
            proceso.pos_hint={'x':0, 'y': pos_y}
            nueva_libre={'inicio':pos_y, 'fin': self.particiones[subscript]['fin'], 'memoria':self.particiones[subscript]['memoria']-proceso.memoria, 'status': Status.LIBRE}
            particion_temp.pop(subscript)
            particion_temp.insert(subscript, {'inicio': proceso.inicio_fin[0], 'fin': proceso.inicio_fin[1], 'memoria': proceso.memoria, 'status': Status.OCUPADA})
            particion_temp.insert(subscript+1, nueva_libre)
            self.add_widget(proceso)
            self.particiones.clear()
            self.particiones=particion_temp.copy()
            if callable(self.agregar_particion):
                self.agregar_particion(self.particiones)


    def desasignacion(self, proceso):
        for index, particion in enumerate(self.particiones):
            if particion['inicio']==proceso.inicio_fin[0] and particion['fin']==proceso.inicio_fin[1]:
                if self.particiones[index-1]['status']==Status.LIBRE and self.particiones[index+1]['status']==Status.LIBRE:
                    inicio = self.particiones[index-1]['inicio']
                    fin = self.particiones[index+1]['fin']
                    memoria = self.particiones[index-1]['memoria'] + particion['memoria'] + self.particiones[index+1]['memoria']
                    nueva_particion={'inicio': inicio, 'fin': fin, 'memoria': memoria, 'status': Status.LIBRE}
                    self.particiones.pop(index+1)
                    self.particiones.pop(index)
                    self.particiones.pop(index-1)
                    self.particiones.insert(index-1, nueva_particion)
                elif self.particiones[index-1]['status']==Status.LIBRE:
                    inicio = self.particiones[index-1]['inicio']
                    memoria = self.particiones[index-1]['memoria'] + particion['memoria']
                    nueva_particion={'inicio': inicio, 'fin': proceso.inicio_fin[1], 'memoria': memoria, 'status': Status.LIBRE}
                    self.particiones.pop(index)
                    self.particiones.pop(index-1)
                    self.particiones.insert(index-1, nueva_particion)
                elif self.particiones[index+1]['status']==Status.LIBRE:
                    fin = self.particiones[index+1]['fin']
                    memoria = particion['memoria'] + self.particiones[index+1]['memoria']
                    nueva_particion={'inicio': proceso.inicio_fin[0], 'fin': fin, 'memoria': memoria, 'status': Status.LIBRE}
                    self.particiones.pop(index+1)
                    self.particiones.pop(index)
                    self.particiones.insert(index, nueva_particion)
                else:
                    particion['status']=Status.LIBRE
                self.remove_widget(proceso)
                proceso.status=Status.TERMINADO
                if callable(self.agregar_particion):
                    self.agregar_particion(self.particiones)
                break

class MainWindow(BoxLayout):
    procs=[]
    event=None
    index=0
    actualizar=None
    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        self.mp=self.ids.memoria_principal
        self.mp.number=self.ids.procesos_no.text
        self.data=self.ids.rvs.data
        self.espera=self.ids.espera.data
        self.part_rv=self.ids.particiones


    def inicio(self):
        self.ids.empezar_boton.disabled=True
        self.procs=self.ids.rvs.procesos
        self.event=Clock.schedule_interval(self.iniciar_peor_ajuste,TIME)
        self.actualizar=Clock.schedule_interval(self.actualizar_no,TIME/2)
        self.mp.agregar_espera=self.agregar_espera
        self.part_rv.agregar_particion(self.mp.particiones)
        self.mp.agregar_particion=self.agregar_particion
        self.event()
        self.actualizar()

    def iniciar_peor_ajuste(self, *args):
        self.mp.peor_ajuste(self.procs[self.index])
        self.data.pop(0)
        self.index+=1
        if self.index>=PROCESOS:
            self.event.cancel()
            self.event=Clock.schedule_interval(self.iniciar_espera,TIME)
            return

    def agregar_espera(self, proceso):
        self.ids.espera.agregar_espera(proceso)

    def agregar_particion(self, particiones):
        self.part_rv.agregar_particion(particiones)

    def iniciar_espera(self, *args):
        if self.ids.espera.procesos:
            proceso=self.ids.espera.procesos[0]
            self.mp.peor_ajuste(proceso)
            self.ids.espera.procesos.pop(0)
            self.espera.pop(0)
        else:
            self.event.cancel()
            for proceso in self.procs:
                print(proceso.id, proceso.text, proceso.memoria, proceso.status)

    def actualizar_no(self, *args):
        self.ids.particiones_no.text='Particiones: '+str(len(self.part_rv.data))
        self.ids.espera_no.text='En espera: '+str(len(self.espera))
        self.ids.procesos_no.text='Procesos: '+str(len(self.data))


class PeorAjusteApp(App):
    def build(self):
        return MainWindow()


if __name__ == '__main__':
    PeorAjusteApp().run()